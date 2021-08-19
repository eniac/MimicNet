package approx.ipv4flow.ecmp;

import approx.ipv4flow.IFlowRoutingTable;

simple ECMPRoutingTable extends IFlowRoutingTable {
    parameters:
        int seed = default(123);

    @class(ECMPRoutingTable);
}
