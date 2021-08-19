#include "MimicDCN.h"
#include "murmur.h"
// KN: These headers are useful for implementing the actual policy for assigning priorities
//#include "transport/HomaTransport.h"
//#include "transport/PriorityResolver.h"

#include <algorithm>
#include <iterator>
#include <cassert>

#define EWMA_WEIGHT 0.3
#define PRESCHEDULED_ING SHRT_MAX
#define PRESCHEDULED_EGR (SHRT_MAX - 1)

using std::ifstream;
using std::istream_iterator;
using std::istringstream;
using std::string;
using std::unique_ptr;
using std::vector;
using std::make_unique;

typedef unique_ptr<vector<double> > Flow;

Define_Module(MimicDCN);

inline int getHostNumInRack(const IPv4Address& addr) {
    return (addr.getDByte(3) / 4);
}

MLMetadata::MLMetadata(const char* library, const char* name,
                       int servers_per_tor, int num_aggs, int num_agg_intfs,
                       int num_tors, int num_features)
            : num_features_(num_features) {
    lastpacket_ = simTime().dbl();
    ewma_ = 0;

    conges_state_ = NO_CONGES;
    cur_bin_start_time_ = 0;
    bin_latency_sum_ = 0;
    bin_num_packets_ = 0;
    bin_num_drops_ = 0;

#ifdef ENABLE_CUDA_LSTM
    prev_drop_ = 0;
    prev_latency_ = 0.001;

    FT_INDEX_CONGES = 0; // 0 - congestion state
    FT_INDEX_SERVER = FT_INDEX_CONGES + CONGES_LEVELS; // server
    FT_INDEX_AGG = FT_INDEX_SERVER + servers_per_tor; // agg
    FT_INDEX_AGGINTF = FT_INDEX_AGG + num_aggs; // agg_intf
    FT_INDEX_TORS = FT_INDEX_AGGINTF + num_agg_intfs; // tor
    FT_INDEX_LAST = FT_INDEX_TORS + num_tors; // time since last packet
#endif

#ifdef ENABLE_PYTHON_LSTM
    input_ = new double[num_features_];

    fprintf(stderr, "Loading %s for %s...\n", name, library);
    PyObject *p_name = PyUnicode_DecodeFSDefault(library);
    
    // Load model library
    p_module_ = PyImport_Import(p_name);

    if (!p_module_) {
        PyErr_Print();
        throw std::runtime_error("Failed to load model library");
    }

    Py_DECREF(p_name);

    // Call the function, setting the return value to p_model_
    p_model_ = PyObject_CallMethod(p_module_, "loadModel", "(s)", name);
    if (p_model_) {
        printf("Loaded model successfully\n");
    } else {
      PyErr_Print();
        throw std::runtime_error("Get of Python model failed");
    }

    // Prefetch getValueDCN function
    p_func_ = PyObject_GetAttrString(p_module_, "getValue");
    if (!p_func_ || !PyCallable_Check(p_func_)) {
        if (PyErr_Occurred()) PyErr_Print();
        throw std::runtime_error("Cannot find function getValueDCN");
    }
#endif
}

MLMetadata::~MLMetadata() {
#ifdef ENABLE_CUDA_LSTM
    cudaFreeHost(input_);
#endif
#ifdef ENABLE_PYTHON_LSTM
    delete input_;
#endif
}

void MLMetadata::updateCongesState(double latency) {
    SimTime cur_time = simTime();
    ++bin_num_packets_;

    bin_latency_sum_ += latency;
    if (latency < LATENCY_DROP_THRESHOLD) {
        ++bin_num_drops_;
    }

    if (cur_time - cur_bin_start_time_ > BIN_WINDOW) {
        if (bin_num_drops_ > bin_num_packets_ / 3) {
            conges_state_ = MAX_CONGES;
        } else {
            double bin_latency_mean = bin_latency_sum_ / bin_num_packets_;
            if (bin_latency_mean > LATENCY_MEDIAN + LATENCY_VARIANCE) {
                if (conges_state_ == NO_CONGES || conges_state_ == INCR_CONGES) {
                    conges_state_ = INCR_CONGES;
                } else if (conges_state_ == MAX_CONGES || conges_state_ == DECR_CONGES) {
                    conges_state_ = DECR_CONGES;
                }
            } else {
                conges_state_ = NO_CONGES;
            }
        }

        bin_num_packets_ = 0;
        cur_bin_start_time_ = cur_time;
        bin_latency_sum_ = 0;
        bin_num_drops_ = 0;
    }
}

MLMetadataTCP::MLMetadataTCP(const char* library, const char* name,
                             int servers_per_tor, int num_aggs,
                             int num_agg_intfs, int num_tors) 
            : MLMetadata(library, name, servers_per_tor, num_aggs,
                         num_agg_intfs, num_tors, 7) {
#ifdef ENABLE_CUDA_LSTM
    FT_INDEX_END = FT_INDEX_LAST + 4; // time since last packet, ewma, last_pred_d, last_pred_l
    cudaMallocHost((void**)&input_, FT_INDEX_END*sizeof(double));
    std::fill(input_, input_ + FT_INDEX_END, 0.0);

    model_ = MimicNetLstmTcp::loadFromHdf5(name);
#endif
}

void MLMetadataTCP::setLastFeatures(double current_time, PacketWrapper* pw) {
#ifdef ENABLE_CUDA_LSTM
    // Discretization before calling the model
    auto last = current_time - lastpacket_;
    int dis_last = (int)(( last - model_->DIS_META_LAST_MIN_) / model_->DIS_META_LAST_STEP_);
    input_[FT_INDEX_LAST] = dis_last;
    lastpacket_ = current_time;
    ewma_ = (1 - EWMA_WEIGHT) * ewma_ + EWMA_WEIGHT * last;
    int dis_ewma = (int)((ewma_ - model_->DIS_META_EWMA_MIN_) / model_->DIS_META_EWMA_STEP_);
    input_[FT_INDEX_LAST + 1] = dis_ewma;
    input_[FT_INDEX_LAST + 2] = prev_drop_;
    int dis_latency = (int)((prev_latency_ - model_->DIS_META_LATENCY_MIN_) / model_->DIS_META_LATENCY_STEP_);
    input_[FT_INDEX_LAST + 3] = dis_latency;
#endif
}

MLMetadataDCTCP::MLMetadataDCTCP(const char* library, const char* name,
                                 int servers_per_tor, int num_aggs,
                                 int num_agg_intfs, int num_tors) 
            : MLMetadata(library, name, servers_per_tor, num_aggs,
                         num_agg_intfs, num_tors, 8) {
#ifdef ENABLE_CUDA_LSTM
    prev_ECN_ = 0;

    FT_INDEX_END = FT_INDEX_LAST + 6; // time since last packet, ewma, ECN, last_pred_d, last_pred_l, last_pred_e
    cudaMallocHost((void**)&input_, FT_INDEX_END*sizeof(double));
    std::fill(input_, input_ + FT_INDEX_END, 0.0);

    model_ = MimicNetLstmDctcp::loadFromHdf5(name);
#endif
}

void MLMetadataDCTCP::setLastFeatures(double current_time, PacketWrapper* pw) {
#ifdef ENABLE_CUDA_LSTM
    // Discretization before calling the model
    auto last = current_time - lastpacket_;
    int dis_last = (int)((last - model_->DIS_META_LAST_MIN_) / model_->DIS_META_LAST_STEP_);
    input_[FT_INDEX_LAST] = dis_last;
    lastpacket_ = current_time;
    ewma_ = (1 - EWMA_WEIGHT) * ewma_ + EWMA_WEIGHT * last;
    int dis_ewma = (int)((ewma_ - model_->DIS_META_EWMA_MIN_) / model_->DIS_META_EWMA_STEP_);
    input_[FT_INDEX_LAST + 1] = dis_ewma;
    input_[FT_INDEX_LAST + 2] = pw->getEcn() ? 1.0 : 0.0;
    input_[FT_INDEX_LAST + 3] = prev_drop_;
    int dis_latency = (int)((prev_latency_ - model_->DIS_META_LATENCY_MIN_) / model_->DIS_META_LATENCY_STEP_);
    input_[FT_INDEX_LAST + 4] = dis_latency;
    input_[FT_INDEX_LAST + 5] = prev_ECN_;
#endif
}

MLMetadataHoma::MLMetadataHoma(const char* library, const char* name,
                               int servers_per_tor, int num_aggs,
                               int num_agg_intfs, int num_tors)
            : MLMetadata(library, name, servers_per_tor, num_aggs,
                         num_agg_intfs, num_tors, 7) {
#ifdef ENABLE_CUDA_LSTM
    FT_INDEX_END = FT_INDEX_LAST + 4; // time since last packet, ewma, last_pred_d, last_pred_l
    cudaMallocHost((void**)&input_, FT_INDEX_END*sizeof(double));
    std::fill(input_, input_ + FT_INDEX_END, 0.0);

    model_ = MimicNetLstmHoma::loadFromHdf5(name);
#endif
}

void MLMetadataHoma::setLastFeatures(double current_time, PacketWrapper* pw) {
#ifdef ENABLE_CUDA_LSTM
    input_[FT_INDEX_LAST] = pw->getPrio();
    input_[FT_INDEX_LAST + 1] = pw->getLength();

    // Discretization before calling the model
    auto last = current_time - lastpacket_;
    int dis_last = (int)(( last - model_->DIS_META_LAST_MIN_) / model_->DIS_META_LAST_STEP_);
    input_[FT_INDEX_LAST + 2] = dis_last;
    lastpacket_ = current_time;
    ewma_ = (1 - EWMA_WEIGHT) * ewma_ + EWMA_WEIGHT * last;
    int dis_ewma = (int)((ewma_ - model_->DIS_META_EWMA_MIN_) / model_->DIS_META_EWMA_STEP_);
    input_[FT_INDEX_LAST + 3] = dis_ewma;
    input_[FT_INDEX_LAST + 4] = prev_drop_;
    int dis_latency = (int)((prev_latency_ - model_->DIS_META_LATENCY_MIN_) / model_->DIS_META_LATENCY_STEP_);
    input_[FT_INDEX_LAST + 5] = dis_latency;
#endif
}


void MimicDCN::initialize() {
    cSimpleModule::initialize();

    // MimicDCN replaces 2 queues and 1 link
    // TODO: parameterize packet size, speed
    double transmission_delay = 
            par("max_queue_len").longValue() * par("packet_size").doubleValue() * 8.0 / par("link_speed").doubleValue();
    max_latency_ = (par("min_link_latency").doubleValue())
                   + (transmission_delay * 2);
    min_latency_ = par("min_link_latency").doubleValue();
    num_intgates_ = gateSize("intport$i");

    servers_per_tor_ = par("servers_per_tor");
    num_aggs_ = par("num_aggs");
    num_agg_intfs_ = par("num_agg_intfs");
    num_tors_ = par("num_tors");

    // Get intermimic distribution and flows
    string intermimic_model = par("intermimic_model");
    ifstream intermimic_fhandle;
    intermimic_fhandle.open(intermimic_model);
    if (!intermimic_fhandle.is_open()) {
        perror("Unable to open inter-mimic flow distribution");
        exit(1);
    }

    string line;
    double ing_shape, ing_loc, ing_scale;
    if (!getline(intermimic_fhandle, line)) {
        perror("Unable to parse inter-mimic flow distribution");
        exit(1);
    }
    auto iss = istringstream(line);
    iss >> ing_shape >> ing_loc >> ing_scale;

    double egr_shape, egr_loc, egr_scale;
    if (!getline(intermimic_fhandle, line)) {
        perror("Unable to parse inter-mimic flow distribution");
        exit(1);
    }
    iss = istringstream(line);
    iss >> egr_shape >> egr_loc >> egr_scale;

    loadAndScheduleInterMimicTraffic(par("ingress_traffic_file"), ing_shape,
                                     ing_loc, ing_scale, true);
    loadAndScheduleInterMimicTraffic(par("egress_traffic_file"), egr_shape,
                                     egr_loc, egr_scale, false);
    parse_ecmp_seeds();

    string ing_model = par("ing_modelprefix");
    string egr_model = par("egr_modelprefix");

#ifdef ENABLE_CUDA_LSTM
    ing_model.append(".hdf5");
    egr_model.append(".hdf5");
#else
    ing_model.append(".ckpt");
    egr_model.append(".ckpt");
#endif

    auto variant = par("variant").stdstringValue();
    if (variant.compare("TCP") == 0) {
        variant_ = TCP;
        ing_ = make_unique<MLMetadataTCP>(par("ing_library"), ing_model.c_str(),
                                          servers_per_tor_, num_aggs_,
                                          num_agg_intfs_, num_tors_);
        egr_ = make_unique<MLMetadataTCP>(par("egr_library"), egr_model.c_str(),
                                          servers_per_tor_, num_aggs_,
                                          num_agg_intfs_, num_tors_);
    } else if (variant.compare("DCTCP") == 0) {
        variant_ = DCTCP;
        ing_ = make_unique<MLMetadataDCTCP>(par("ing_library"), ing_model.c_str(),
                                            servers_per_tor_, num_aggs_,
                                            num_agg_intfs_, num_tors_);
        egr_ = make_unique<MLMetadataDCTCP>(par("egr_library"), egr_model.c_str(),
                                            servers_per_tor_, num_aggs_,
                                            num_agg_intfs_, num_tors_);
    } else if (variant.compare("Homa") == 0) {
        variant_ = Homa;
        ing_ = make_unique<MLMetadataHoma>(par("ing_library"), ing_model.c_str(),
                                           servers_per_tor_, num_aggs_,
                                           num_agg_intfs_, num_tors_);
        egr_ = make_unique<MLMetadataHoma>(par("egr_library"), egr_model.c_str(),
                                           servers_per_tor_, num_aggs_,
                                           num_agg_intfs_, num_tors_);
    } else {
        throw std::runtime_error("Unsupported variant: " + variant);
    }
}

void MimicDCN::finish() {
    // TODO: Causes a segfault, likely due to pythoninterp being freed first
    // Py_DECREF(p_module_);
    // Py_DECREF(p_model_);
    // Py_DECREF(p_func_);
}

struct active_flow_comp {
    bool operator() (const Flow& lhs, const Flow& rhs) const {
        return lhs->at(1) < rhs->at(1);
    }
};

void MimicDCN::loadAndScheduleInterMimicTraffic(string file_name, double shape,
                                                double loc, double scale,
                                                bool isIncoming) {
    ifstream interval_fhandle;
    interval_fhandle.open(file_name);
    if (!interval_fhandle.is_open()) {
        perror("Unable to open inter-mimic flow information");
        exit(1);
    }

    int total_inter_mimic_flows = 0;

    string line;
    unique_ptr<vector<double>> next_flow;
    double current_time = 0;
    double next_time;

    vector<Flow> active_flows;

    if (getline(interval_fhandle, line)) {
        auto line_iss = istringstream(line);
        next_flow = make_unique<vector<double> >(
                istream_iterator<double>{line_iss}, istream_iterator<double>());
        next_time = next_flow->at(0);
        next_flow->push_back(0); // The last element denotes the number of packets sent
    }

    // KN: Getting the PriorityResolver is useful for implementing the actual priority assignment
    //HomaTransport* homaTransport = dynamic_cast<HomaTransport*>(getModuleByPath("cluster[1].host[0].transportScheme"));
    //const PriorityResolver* prioResolver = homaTransport->getPriorityResolver();

    while (next_flow || !active_flows.empty()) {
        // TODO: automate me!
        //shape 3.856471, scale 0.000218, loc -0.000212
        double time_elapsed = pareto_shifted(shape, scale, loc, 1);
        current_time += time_elapsed;

        // add any new flows
        while (next_flow && next_time <= current_time) {
            active_flows.push_back(move(next_flow));
            push_heap(active_flows.begin(), active_flows.end(),
                      active_flow_comp());
            if (getline(interval_fhandle, line)) {
                auto line_iss = istringstream(line);
                next_flow = make_unique<vector<double> >(
                        istream_iterator<double>{line_iss},
                        istream_iterator<double>());
                next_flow->push_back(0); // The last element denotes the number of packets sent
                next_time = next_flow->at(0);
            }
        }
        // remove expired flows
        while (!active_flows.empty()) {
            if (active_flows.front()->at(1) <= current_time){
                pop_heap(active_flows.begin(), active_flows.end(),
                         active_flow_comp());
                active_flows.pop_back();
            } else {
                break;
            }
        }

        if (active_flows.empty()) {
            continue;
        }

        total_inter_mimic_flows += 1;

        // schedule the packet
        // start, end, dst_server, dst_rack, src_server, src_rack, agg, agg_intf
        int rand_flow_index = rand() % active_flows.size();
        PrescheduledMsg* pre_scheduled_callback = new PrescheduledMsg;
        pre_scheduled_callback->setDst_server(active_flows[rand_flow_index]->at(2));
        pre_scheduled_callback->setDst_rack(active_flows[rand_flow_index]->at(3));
        pre_scheduled_callback->setSrc_server(active_flows[rand_flow_index]->at(4));
        pre_scheduled_callback->setSrc_rack(active_flows[rand_flow_index]->at(5));
        pre_scheduled_callback->setAgg(active_flows[rand_flow_index]->at(6));
        pre_scheduled_callback->setAgg_intf(active_flows[rand_flow_index]->at(7));

        // For DCTCP:
        pre_scheduled_callback->setEcn(false); // This shouldn't matter

        // For Homa:
        // TODO: make sure that this code (copied from Homa branch) is correct
        const int max_payload_size = 1441;
        const int header_size = 31;
        int payload_size = std::min(max_payload_size, (int)active_flows[rand_flow_index]->at(8));
        if (payload_size == 0) {
            continue;
        }
        pre_scheduled_callback->setLength(payload_size + header_size);

        if (active_flows[rand_flow_index]->at(9) < 7) { // REQUEST or UNSCHED
            pre_scheduled_callback->setPriority(0);
        } else { // SCHED
            pre_scheduled_callback->setPriority(7);
        }

        active_flows[rand_flow_index]->at(8) -= payload_size;
        active_flows[rand_flow_index]->at(9) += 1;

        if (isIncoming) {
            pre_scheduled_callback->setKind(PRESCHEDULED_ING);
        } else {
            pre_scheduled_callback->setKind(PRESCHEDULED_EGR);
        }
        scheduleAt(SimTime(current_time), pre_scheduled_callback);
    }
    interval_fhandle.close();

    std::cout << "Number of inter-mimic flows = " << total_inter_mimic_flows << std::endl;
}

void MimicDCN::parse_ecmp_seeds() {
    istringstream tor_iss(par("torEcmpSeeds").stdstringValue());
    vector<string> tor_seeds(istream_iterator<string>{tor_iss},
                             istream_iterator<string>());

    for (auto iter = tor_seeds.begin(); iter != tor_seeds.end(); ++iter) {
        tor_seeds_.push_back(atoi(iter->c_str()));
    }

    istringstream agg_iss(par("aggEcmpSeeds").stdstringValue());
    vector<string> agg_seeds(istream_iterator<string>{agg_iss},
                             istream_iterator<string>());

    for (auto iter = agg_seeds.begin(); iter != agg_seeds.end(); ++iter) {
        agg_seeds_.push_back(atoi(iter->c_str()));
    }

    assert(agg_seeds_.size() == num_aggs_);
    assert(tor_seeds_.size() == num_tors_);
}

double MimicDCN::predict_packet_helper(IPv4Datagram* dgram, int aggregation,
                                       int interface, MLMetadata* meta,
                                       bool isIncoming) {
    IPv4Address destAddr = dgram->getDestAddress();
    int destServ = getHostNumInRack(destAddr);
    int destToR = destAddr.getDByte(2);

    IPv4Address srcAddr = dgram->getSrcAddress();
    int srcServ = getHostNumInRack(srcAddr);
    int srcToR = srcAddr.getDByte(2);

    IPv4DatagramWrapper pw(dgram);
    double lat = predict(&pw, destServ, destToR, srcServ, srcToR, aggregation,
                         interface, meta, isIncoming);
    return lat;
}

// Incoming Features:
//       Time since last ingress packet, Network State, Destination Server, ingress agg, ingress agg interface, Destination ToR, EWMA packet interarrival time
// Outgoing features:
//       Time since last egress packet, Network State, Origin Server, egress agg, egress agg interface, origin ToR, EWMA packet interarrival time

#ifdef ENABLE_CUDA_LSTM
double MimicDCN::predict(PacketWrapper* pkt, int destServ, int destToR,
                         int srcServ, int srcToR, int aggregation,
                         int interface, MLMetadata* meta, bool isIncoming) {

    // time difference in seconds
    double current_time = simTime().dbl();

    // we one-hot the array by setting everything to 0 and then setting 1s
    double *conges_ptr;
    conges_ptr = meta->input_ + meta->FT_INDEX_CONGES + meta->conges_state_;
    *conges_ptr = 1.0;

    double *server_ptr;
    double *agg_ptr;
    double *aggintf_ptr;
    double *tor_ptr;

    if (isIncoming) {
        // Server
        server_ptr = meta->input_ + meta->FT_INDEX_SERVER + (destServ);
        *server_ptr = 1.0;
        // Agg
        agg_ptr = meta->input_ + meta->FT_INDEX_AGG + aggregation;
        *agg_ptr = 1.0;
        // Agg interface
        aggintf_ptr = meta->input_ + meta->FT_INDEX_AGGINTF + interface;
        *aggintf_ptr = 1.0;
        // ToR
        tor_ptr = meta->input_ + meta->FT_INDEX_TORS + destToR;
        *tor_ptr = 1.0;
    } else {
        // Server
        server_ptr = meta->input_ + meta->FT_INDEX_SERVER + (srcServ);
        *server_ptr = 1.0;
        // Agg
        agg_ptr = meta->input_ + meta->FT_INDEX_AGG + aggregation;
        *agg_ptr = 1.0;
        // Agg interface
        aggintf_ptr = meta->input_ + meta->FT_INDEX_AGGINTF + interface;
        *aggintf_ptr = 1.0;
        // ToR
        tor_ptr = meta->input_ + meta->FT_INDEX_TORS + srcToR;
        *tor_ptr = 1.0;
    }

    meta->setLastFeatures(current_time, pkt);

    bool drop;
    double latency;
    bool ecn;
    MLMetadataTCP* m_tcp;
    MLMetadataDCTCP* m_dctcp;
    MLMetadataHoma* m_homa;

    switch(variant_) {
        case TCP:
            m_tcp = dynamic_cast<MLMetadataTCP*>(meta);
            m_tcp->model_->getValue(&drop, &latency, meta->input_);
            // De-discretize the results
            latency = m_tcp->model_->DIS_META_LATENCY_MIN_ \
                    + ((int)latency) * m_tcp->model_->DIS_META_LATENCY_STEP_;
            break;
        case DCTCP:
            m_dctcp = dynamic_cast<MLMetadataDCTCP*>(meta);
            m_dctcp->model_->getValue(&drop, &latency, &ecn, meta->input_);
            // De-discretize the results
            latency = m_dctcp->model_->DIS_META_LATENCY_MIN_ \
                    + ((int)latency) * m_dctcp->model_->DIS_META_LATENCY_STEP_;

            m_dctcp->prev_ECN_ = ecn;
            if (ecn) {
                pkt->setEcn();
            }
            break;
        case Homa:
            m_homa = dynamic_cast<MLMetadataHoma*>(meta);
            m_homa->model_->getValue(&drop, &latency, meta->input_);
            // De-discretize the results
            latency = m_homa->model_->DIS_META_LATENCY_MIN_ \
                    + ((int)latency) * m_homa->model_->DIS_META_LATENCY_STEP_;
            break;
        default:
            throw std::runtime_error("Unsupported variant: " + variant_);
    }

    meta->prev_drop_ = drop;
    meta->prev_latency_ = latency;

    *conges_ptr = 0;
    *server_ptr = 0;
    *agg_ptr = 0;
    *aggintf_ptr = 0;
    *tor_ptr = 0;

    if (drop) {
#ifdef DEBUG
        fprintf(stderr, "**DROPPED** Deciding to drop packet\n");
#endif
        meta->prev_drop_ = 1;
        meta->prev_latency_ = 0;
        return -1;
    }
#ifdef DEBUG
    fprintf(stderr, "**ROUTED** Incurring delay %f\n", latency);
#endif
    meta->prev_drop_ = 0;
    if (latency < min_latency_) {
    	meta->prev_latency_ = min_latency_;
        return min_latency_;
    }
    if (latency > max_latency_) {
        meta->prev_latency_ = max_latency_;
        return max_latency_;
    }
    return latency;
}
#endif

#ifdef ENABLE_PYTHON_LSTM
double MimicDCN::predict(PacketWrapper* pkt, int destServ, int destToR,
                         int srcServ, int srcToR, int aggregation,
                         int interface, MLMetadata* meta, bool isIncoming) {
    // time in seconds
    double current_time = simTime().dbl();

    meta->input_[0] = static_cast<double>(meta->conges_state_);

    if (isIncoming) {
        meta->input_[1] = static_cast<double>(destServ);
        meta->input_[2] = static_cast<double>(aggregation);
        meta->input_[3] = static_cast<double>(interface);
        meta->input_[4] = static_cast<double>(destToR);
    } else {
        meta->input_[1] = static_cast<double>(srcServ);
        meta->input_[2] = static_cast<double>(aggregation);
        meta->input_[3] = static_cast<double>(interface);
        meta->input_[4] = static_cast<double>(srcToR);
    }

    int current_index = 5;
    if (variant_ == Homa) {
        meta->input_[current_index++] = pkt->getPrio();
        meta->input_[current_index++] = pkt->getLength();
    }
    meta->input_[current_index++] = current_time - meta->lastpacket_;
    meta->lastpacket_ = current_time;
    meta->ewma_ = (1 - EWMA_WEIGHT) * meta->ewma_ + EWMA_WEIGHT * meta->input_[5];
    meta->input_[current_index++] = meta->ewma_;
    if (variant_ == DCTCP) {
        meta->input_[current_index] = pkt->getEcn();
    }

#ifdef DEBUG
    fprintf(stderr, "Features: ");
    for (int i=0; i < meta->num_features_; i++) {
        if (i==0){
            fprintf(stderr, "%.16f ", meta->input_[i]);
        }
        else {
            fprintf(stderr, "%f ", meta->input_[i]);
        }
    }
    fprintf(stderr, "\n");
#endif

    double latency_predict;

    PyObject* fwdArgs = PyTuple_New(meta->num_features_ + 1);
    Py_INCREF(meta->p_model_);
    PyTuple_SetItem(fwdArgs, 0, meta->p_model_);

    for (int i = 0; i < meta->num_features_; ++i) {
        // Set feature arguments
        PyObject* feature = PyFloat_FromDouble(meta->input_[i]);
        if (!feature) {
            Py_DECREF(fwdArgs);
            Py_DECREF(meta->p_module_);
            throw std::invalid_argument("Cannot convert an input");
        }
        // feature reference stolen here:
        // Put remaining arguments, the features, into tuple
        PyTuple_SetItem(fwdArgs, i+1, feature);
    }

    PyObject* delayVal = PyObject_CallObject(meta->p_func_, fwdArgs);
    Py_DECREF(fwdArgs);

    if (delayVal != NULL) {
        double drop_predict = PyFloat_AsDouble(PyTuple_GetItem(delayVal, 0));
        if (drop_predict > 0.5) {
#ifdef DEBUG
            fprintf(stderr, "**DROPPED** Deciding to drop packet\n");
#endif
            return -1.0;
        }

        latency_predict = PyFloat_AsDouble(PyTuple_GetItem(delayVal, 1));

        if (variant_ == DCTCP) {
            double ecn_predict = PyFloat_AsDouble(PyTuple_GetItem(delayVal, 2));
            if (ecn_predict >= 0.5) {
                pkt->setEcn();
            }
        }
        Py_DECREF(delayVal);
    } else {
        Py_DECREF(meta->p_module_);
        PyErr_Print();
        throw std::runtime_error("getValue call failed");
    }

#ifdef DEBUG
    fprintf(stderr, "**ROUTED** Incurring delay %f\n", latency_predict);
#endif
    if (latency_predict < min_latency_) {
        return min_latency_;
    }
    if (latency_predict > max_latency_) {
        return max_latency_;
    }
    return latency_predict;
}
#endif

void MimicDCN::handleMessage(cMessage *msg) {
    if (msg->isSelfMessage()) {
        if (msg->getKind() == PRESCHEDULED_ING){
            PrescheduledMsg *pm = static_cast<PrescheduledMsg*>(msg);
            PreschedWrapper pw(pm);
            double latency = predict(&pw, pm->getDst_server(), pm->getDst_rack(),
                                     pm->getSrc_server(), pm->getSrc_rack(),
                                     pm->getAgg(), pm->getAgg_intf(),
                                     ing_.get(), true);
            delete msg;

            if (latency < 0) {
                ing_->updateCongesState(0);
            } else {
                ing_->updateCongesState(latency);
            }
        } else if (msg->getKind() == PRESCHEDULED_EGR) {
            PrescheduledMsg *pm = static_cast<PrescheduledMsg*>(msg);
            PreschedWrapper pw(pm);
            double latency = predict(&pw, pm->getDst_server(), pm->getDst_rack(),
                                     pm->getSrc_server(), pm->getSrc_rack(),
                                     pm->getAgg(), pm->getAgg_intf(),
                                     egr_.get(), false);
            delete msg;

            if (latency < 0) {
                egr_->updateCongesState(0);
            } else {
                egr_->updateCongesState(latency);

                //TODO: Route dummy packets to core switches here?
                //EtherFrame* dummy = new EtherFrame("dummy", kind=(SHRT_MAX-2));
                //dummy->setDest(MACAddress::BROADCAST_ADDRESS);
                //int out_intf = (int)flow_info[5];
                //simtime_t busyUntil = gate("extport$o", out_intf)->getTransmissionChannel()->getTransmissionFinishTime();
                //if (busyUntil <= simTime()) {
                //  sendDelayed(msg, simTime()+SimTime(latency), "extport$o", out_intf);
                //} else {
                //  sendDelayed(msg, busyUntil - simTime() + SimTime(latency), "extport$o", out_intf);
                //}
            }
        } else {
            routeMsg(msg);
        }
    } else {
        cGate *arrgate = msg->getArrivalGate();
        EtherFrame* frame = dynamic_cast<EtherFrame*>(msg);
        if (frame == NULL) throw cRuntimeError(msg, "Expected Etherframe");
        cPacket* frame_contents = frame->getEncapsulatedPacket();
        if (frame_contents == NULL) throw cRuntimeError(msg, "Got NULL Packet");
        IPv4Datagram* dgram = dynamic_cast<IPv4Datagram*>(frame_contents);
        if (dgram == NULL) {
            ARPPacket* arp_packet = dynamic_cast<ARPPacket*>(frame_contents);
            if (arp_packet == NULL) {
                throw cRuntimeError(msg, "Expected IPv4 Packet");
            } else {
                handleARPReq(msg, arp_packet, frame);
                return;
            }
        }

        if (arrgate->isName("intport$i")) {
            handleEgress(msg, dgram, frame);
        } else {
            handleIngress(msg, dgram, arrgate->getIndex());
        }
    }
}

void MimicDCN::routeMsg(cMessage *msg) {
    short out_intf = msg->getKind();

    if (out_intf < num_intgates_) {
        // Ingress
        simtime_t busyUntil = gate("intport$o", out_intf)->getTransmissionChannel()->getTransmissionFinishTime();
        if (busyUntil <= simTime()) {
            send(msg, "intport$o", out_intf);
        } else {
            sendDelayed(msg, busyUntil - simTime(), "intport$o", out_intf);
        }
    } else {
        // Egress
        out_intf -= num_intgates_;

        simtime_t busyUntil = gate("extport$o", out_intf)->getTransmissionChannel()->getTransmissionFinishTime();
        if (busyUntil <= simTime()) {
            send(msg, "extport$o", out_intf);
        } else {
            sendDelayed(msg, busyUntil-simTime(), "extport$o", out_intf);
        }
    }
}

void MimicDCN::handleARPReq(cMessage *msg, ARPPacket* arp_packet,
                             EtherFrame* frame) {
    const MACAddress& orig_src_mac = arp_packet->getSrcMACAddress();
    const IPv4Address& orig_src_ip = arp_packet->getSrcIPAddress();
    const IPv4Address& orig_dest_ip = arp_packet->getDestIPAddress();

    arp_packet->setSrcMACAddress(MACAddress::BROADCAST_ADDRESS);
    arp_packet->setDestMACAddress(orig_src_mac);
    arp_packet->setSrcIPAddress(orig_dest_ip);
    arp_packet->setDestIPAddress(orig_src_ip);

    frame->setSrc(MACAddress::BROADCAST_ADDRESS);
    frame->setDest(orig_src_mac);

    cGate *arrgate = msg->getArrivalGate();
    string outgate_name = arrgate->getBaseName();
    outgate_name += "$o";
    int intf_index = arrgate->getIndex();
    string outgate_fullname = outgate_name + "[" + std::to_string(intf_index) + "]";

    simtime_t busyUntil = gate(outgate_name.c_str(), intf_index)->getTransmissionChannel()->getTransmissionFinishTime();
    if (busyUntil <= simTime()) {
        send(msg, outgate_name.c_str(), intf_index);
    } else {
        sendDelayed(msg, busyUntil-simTime(), outgate_name.c_str(), intf_index);
    }
}

void MimicDCN::handleEgress(cMessage *msg, IPv4Datagram* dgram,
                            EtherFrame* frame) {
    IPv4Address srcAddr = dgram->getSrcAddress();
    IPv4Address destAddr = dgram->getDestAddress();

    int srcSubtree = srcAddr.getDByte(1);
    int destSubtree = destAddr.getDByte(1);

    if (srcSubtree == destSubtree) {
        // Just drop it
        delete msg;
        return;
    }

    int srcToR = srcAddr.getDByte(2);
    int aggregation;
    int intf;

    // Cast to Segment
    if (dgram->getTransportProtocol() == IP_PROT_TCP) {
        TCPSegment* tcpSegment = check_and_cast<TCPSegment*>(dgram->getEncapsulatedPacket());
        unsigned short srcPort = tcpSegment->getSrcPort();
        unsigned short destPort = tcpSegment->getDestPort();

        aggregation = ecmp_helper(num_aggs_, tor_seeds_[srcToR], srcAddr, srcPort, destAddr, destPort);
        intf = ecmp_helper(num_agg_intfs_, agg_seeds_[aggregation], srcAddr, srcPort, destAddr, destPort);
    } else if (dgram->getTransportProtocol() == IP_PROT_UDP) {
        UDPPacket* udpPacket = check_and_cast<UDPPacket*>(dgram->getEncapsulatedPacket());
        unsigned short srcPort = udpPacket->getSourcePort();
        unsigned short destPort = udpPacket->getDestinationPort();

        aggregation = ecmp_helper(num_aggs_, tor_seeds_[srcToR], srcAddr, srcPort, destAddr, destPort);
        intf = ecmp_helper(num_agg_intfs_, agg_seeds_[aggregation], srcAddr, srcPort, destAddr, destPort);
    } else {
        aggregation = ecmp_helper(num_aggs_, tor_seeds_[srcToR], srcAddr, destAddr);
        intf = ecmp_helper(num_agg_intfs_, agg_seeds_[aggregation], srcAddr, destAddr);
    }

    double prediction = predict_packet_helper(dgram, aggregation, intf,
                                              egr_.get(), false);
    if (prediction < 0) {
        egr_->updateCongesState(0);

        delete msg;
    } else {
        egr_->updateCongesState(prediction);

        short out_intf = (agg_seeds_.size() * aggregation) + intf;
        frame->setDest(MACAddress::BROADCAST_ADDRESS);
        msg->setKind(num_intgates_ + out_intf);
        scheduleAt(simTime() + SimTime(prediction), msg);
    }
}

void MimicDCN::handleIngress(cMessage *msg, IPv4Datagram* dgram,
                              const int agg_gate) {
    // This number represents the ingress to the MimicDCN which
    // conflates aggregation switches and interfaces
    int aggregation = agg_gate / num_agg_intfs_;
    int intf = agg_gate % num_agg_intfs_;

    double prediction = predict_packet_helper(dgram, aggregation, intf,
                                              ing_.get(), false);
    if (prediction < 0) {
        ing_->updateCongesState(0);

        delete msg;
    } else {
        ing_->updateCongesState(prediction);

        IPv4Address destAddr = dgram->getDestAddress();
        short out_intf = (destAddr.getDByte(2)*4) + (destAddr.getDByte(3)/4);
        EtherFrame* frame = dynamic_cast<EtherFrame*>(msg);
        frame->setDest(MACAddress::BROADCAST_ADDRESS);
        msg->setKind(out_intf);

        scheduleAt(simTime() + SimTime(prediction), msg);
    }
}

int MimicDCN::ecmp(const string& flowBin, int size, int seed) {
    return positiveMod(murmur3_32((const unsigned char*)flowBin.data(),
                                  flowBin.size(), seed), size);
}

template <typename... FlowT>
int MimicDCN::ecmp_helper(int size, int seed, FlowT... flow) {
    string flowBin = convertToFlowBin(flow...);
    return ecmp(flowBin, size, seed);
}

string MimicDCN::convertToFlowBin(const IPv4Address& srcIP,
                                  unsigned short srcPort,
                                  const IPv4Address& destIP,
                                  unsigned short destPort) {
    string flowBin(12, 0);
    *(int*)flowBin.data() = srcIP.getInt();
    *(unsigned short*)(flowBin.data() + 4) = srcPort;
    *(int*)(flowBin.data() + 6) = destIP.getInt();
    *(unsigned short*)(flowBin.data() + 10) = destPort;
    return flowBin;
}

string MimicDCN::convertToFlowBin(const IPv4Address& srcIP,
                                  const IPv4Address& destIP) {
    string flowBin(8, 0);
    *(int*)flowBin.data() = srcIP.getInt();
    *((int*)flowBin.data() + 1) = destIP.getInt();
    return flowBin;
}
