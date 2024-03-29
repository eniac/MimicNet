//==============================================================
//   SIM_STD.MSG  - part of
//                     OMNeT++/OMNEST
//            Discrete System Simulation in C++
//
//  Author: Andras Varga
//
//==============================================================

//--------------------------------------------------------------
// Copyright (C) 1992-2005 Andras Varga
//
//  This file is distributed WITHOUT ANY WARRANTY. See the file
//  `license' for details on this and other legal matters.
//--------------------------------------------------------------


//
// Property descriptors for the simkernel classes.
// Usage: opp_msgc -Xnc -Xns sim_std.msg
//

cplusplus
{{

#ifdef _MSC_VER
#  pragma warning(disable:4996)  // deprecation (cLinkedList)
#endif

#ifdef __GNUC__
#  pragma GCC diagnostic ignored "-Wdeprecated-declarations"
#endif

NAMESPACE_BEGIN

//
// Register enums from the sim. kernel
//
typedef cPar::Type   cPar_Type;
typedef cGate::Type  cGate_Type;

Register_Enum(cPar_Type,  (cPar::BOOL, cPar::DOUBLE, cPar::LONG, cPar::STRING, cPar::XML));
Register_Enum(cGate_Type, (cGate::INPUT, cGate::OUTPUT, cGate::INOUT));

typedef cFigure::LineStyle  cFigure_LineStyle;
typedef cFigure::CapStyle   cFigure_CapStyle;
typedef cFigure::JoinStyle  cFigure_JoinStyle;
typedef cFigure::ArrowHead  cFigure_ArrowHead;
typedef cFigure::Anchor     cFigure_Anchor;
typedef cFigure::Alignment  cFigure_Alignment;

namespace aux {
#define cF cFigure
Register_Enum(cFigure_LineStyle, (cF::LINE_SOLID, cF::LINE_DOTTED, cF::LINE_DASHED));
Register_Enum(cFigure_CapStyle,  (cF::CAP_BUTT, cF::CAP_SQUARE, cF::CAP_ROUND));
Register_Enum(cFigure_JoinStyle, (cF::JOIN_BEVEL, cF::JOIN_MITER, cF::JOIN_ROUND));
Register_Enum(cFigure_ArrowHead, (cF::ARROW_NONE, cF::ARROW_SIMPLE, cF::ARROW_TRIANGLE, cF::ARROW_BARBED));
Register_Enum(cFigure_Anchor,    (cF::ANCHOR_CENTER, cF::ANCHOR_N, cF::ANCHOR_E, cF::ANCHOR_S, cF::ANCHOR_W, cF::ANCHOR_NW, cF::ANCHOR_NE, cF::ANCHOR_SE, cF::ANCHOR_SW));
Register_Enum(cFigure_Alignment, (cF::ALIGN_LEFT, cF::ALIGN_RIGHT, cF::ALIGN_CENTER));
#undef cF
};

//
// Define operator<< for some classes
//
inline std::ostream& operator<<(std::ostream& os, const cDisplayString& d) {
    return os << "\"" << d.str() << "\"";
}

typedef cDensityEstBase::Cell cDensityEstBase_Cell;
inline std::ostream& operator<<(std::ostream& os, const cDensityEstBase::Cell& cell) {
    return os << "[" << cell.lower << ", " << cell.upper << ")  ==>  " << cell.value << " (" << cell.relativeFreq << ")";
}

typedef cFigure::Point Point;
inline std::ostream& operator<<(std::ostream& os, const cFigure::Point& p) {
    return os << "(" << p.x << ", " << p.y << ")";
}

inline std::ostream& operator<<(std::ostream& os, const cFigure::Rectangle& r) {
    return os << "(" << r.x << ", " << r.y << ", w=" << r.width << ", h=" << r.height << ")";
}
// typedef cFigure::Rectangle Rectangle; // conflicts with MINGW's WINGDI.H Rectangle
#define Rectangle cFigure::Rectangle


typedef cFigure::Color Color;
inline std::ostream& operator<<(std::ostream& os, const cFigure::Color& c) {
    return os << "(" << (int)c.red << "," << (int)c.green << "," << (int)c.blue << ")";
}

typedef cFigure::Font Font;
static std::ostream& operator<<(std::ostream& os, const cFigure::Font& f)
{
    os << "(" << (f.typeface.empty()? "<default>" : f.typeface) << ", ";
    os << (int)f.pointSize << " pt";
    if (!f.style)
        os << ", none";
    else {
        os << ",";
        if (f.style & cFigure::FONT_BOLD)  os << " bold";
        if (f.style & cFigure::FONT_ITALIC)  os << " italic";
        if (f.style & cFigure::FONT_UNDERLINE)  os << " underline";
    }
    os << ")";
    return os;
}

/* XXX currently unused
typedef std::vector<std::string> StringVector;
static std::ostream& operator<<(std::ostream& os, const std::vector<std::string>& v)
{
    os << "[";
    for (int i = 0; i < (int)v.size(); i++) {
        if (i > 0) os << ", ";
        os << v[i];
    }
    os << "]";
    return os;
}
*/

//
// This function is to be referenced from sim. kernel classes, to force the
// linker to include this file in executables
//
void std_sim_descriptor_dummy() {}

}}

enum cPar_Type;
enum cGate_Type;

enum cFigure_LineStyle;
enum cFigure_CapStyle;
enum cFigure_JoinStyle;
enum cFigure_ArrowHead;
enum cFigure_Anchor;
enum cFigure_Alignment;

struct cDensityEstBase_Cell;

struct Point;
struct Rectangle;
struct Color;
struct Font;

class noncobject StringVector;

class cObject
{
    @icon(cogwheel);
    string className @group(base) @hint("C++ class name") @eventlog(skip);
    string fullName @group(base) @hint("If object is part of a module/gate vector: name with index");
    string fullPath @group(base) @hint("Hierarchical name, composed of full names of this object and its owners/parents") @eventlog(skip);
    string info @getter(info) @group(base) @hint("Text provided by the object's \"info\" method") @eventlog(skip);
    string detailedInfo @getter(detailedInfo) @group(base) @hint("Text provided by the object's \"detailedInfo\" method") @eventlog(skip);
}

class cNamedObject extends cObject
{
    string name @group(base) @editable @hint("An editable string attribute of the object, also used for fullName and fullPath");
}

class cOwnedObject extends cNamedObject
{
    cObject *owner @group(base) @hint("Module or container this object belongs to") @eventlog(skip);
}

class cNoncopyableOwnedObject extends cOwnedObject
{
}

class cDefaultList extends cNoncopyableOwnedObject
{
    cOwnedObject *defaultList[] @getter(defaultListGet) @sizeGetter(defaultListSize) @group(owned objects) @hint("List of objects directly held by this component");
}

class cDisplayString extends void
{
    string value @getter(str) @setter(parse) @editable @hint("The editable display string itself");
}

class cProperty extends cObject
{
    bool isImplicit @getter(isImplicit) @group(fields);
    string index @group(fields);
    string value @getter(info) @hint("Name and value");
}

class cProperties
{
    cProperty *contents[] @getter(get) @sizeGetter(getNumProperties) @hint("The property list");
}

class cPar extends cObject;
class cComponentType extends cOwnedObject;

class cComponent extends cDefaultList
{
    bool isModule @getter(isModule) @group(fields) @hint("Whether this component is a module or a channel");
    cComponentType *componentType @group(fields) @hint("The object that represents the type declaration for this component");
    cPar par[] @getter(par) @sizeGetter(getNumParams) @label(parameters) @group(parameters, gates) @hint("Parameters");
    cProperties *props @getter(getProperties) @label("properties") @group(parameters, gates) @hint("Properties");
}

class cChannel extends cComponent
{
    @icon(channel);
    cDisplayString displayString @group(fields) @hint("Controls appearance of this channel in the GUI");
}

class cIdealChannel extends cChannel
{
    // nothing special
}

class cDelayChannel extends cChannel
{
    // nothing special
}

class cDatarateChannel extends cChannel
{
    // Note: no need to spell out delay etc, they come from cComponent parameters
    bool isBusy @getter(isBusy) @group(fields) @hint("If channel is currently transmitting");
    simtime_t transmissionFinishTime @group(fields) @hint("If busy: when currently active transmissions will finish");
}

class cGate extends cObject;

class cModule extends cComponent
{
    @icon(compound);
    int id @group(fields) @hint("Unique module ID -- IDs of deleted modules are not issued again");
    bool isSimple @getter(isSimple) @group(fields) @hint("Whether this is a simple module");
    bool isVector @getter(isVector) @group(fields) @hint("Whether this module is part of a module vector");
    int index @group(fields) @hint("If vector: index of this module in its module vector");
    int size @getter(size) @group(fields) @hint("If vector: size of module vector this module belongs to");
    cDisplayString displayString @group(fields) @hint("Controls appearance of this module in the GUI");
    cGate *gate[] @getter(getGateCount) @sizeGetter(gateCount) @getter(gateByOrdinal) @group(parameters, gates) @label(gates) @hint("Module gates");
}

class cSimpleModule extends cModule
{
    @icon(simple);
    bool isTerminated @getter(isTerminated) @group(fields) @hint("Whether this module has terminated");
    bool usesActivity @getter(usesActivity) @group(activity) @hint("Whether this simple module was programmed using the \"activity\" or the \"handleMessage\" C++ method");
    unsigned int stackSize @group(activity) @hint("If module uses \"activity\": stack size allocated for this module -- zero means info not available");
    unsigned int stackUsage @group(activity) @hint("If module uses \"activity\": stack actually used by this module -- zero means info not available");
}

//TODO: use @icon(placeholder) for cPlaceholderModule

//----

class cComponentType extends cNoncopyableOwnedObject
{
}

class cModuleType extends cComponentType
{
    bool isNetwork @getter(isNetwork) @group(fields) @hint("Whether this module type can be used as toplevel module");
}

class cChannelType extends cComponentType
{
}

class cRegistrationList extends cNamedObject
{
    cObject *contents[] @getter(get) @sizeGetter(size) @hint("Contained objects");
}

//----

class cGate extends cObject
{
    @icon(gate);
    char type @group(fields) @enum(cGate_Type) @hint("Gate type");
    int id @group(fields) @hint("Gate id, unique within this module");
    bool isVector @getter(isVector) @group(fields) @hint("Whether this gate is part of a gate vector");
    int index @group(fields) @hint("If vector: index of this gate within its gate vector");
    bool deliverOnReceptionStart @group(fields) @hint("Only for simple module input gates, and if message transmission duration is nonzero: whether messages arriving on this gate will be given to the module at the start or the end of the reception");

    cChannel *channel @group(connection) @hint("Channel object associated with the connection");
    cGate *previousGate @group(connection) @hint("The gate this one is connected to -- for output gates this points out of this module, and for input gates it points inside");
    cGate *nextGate @group(connection) @hint("The gate whose \"previousGate\" is this gate -- note that \"previous\" and \"next\" correspond to the direction of messages");
    cGate *pathStartGate @group(connection) @hint("The last gate in the \"previousGate->previousGate->previousGate...\" chain");
    cGate *pathEndGate @group(connection) @hint("The last gate in the \"nextGate->nextGate->nextGate...\" chain");
    bool isConnectedOutside @getter(isConnectedOutside) @group(connection) @hint("For an output gate this checks nextGate, and previousGate for an input gate");
    bool isConnectedInside @getter(isConnectedInside) @group(connection) @hint("For an input gate this checks nextGate, and previousGate for an output gate");
    bool isConnected @getter(isConnected) @group(connection) @hint("Whether the gate is fully connected -- both inside and outside for a compound module gate, and outside for a simple module gate");
    bool isPathOK @getter(isPathOK) @group(connection) @hint("The chain of connections is OK if it starts and ends at a simple module");
}

//----

class cArray extends cOwnedObject
{
    @icon(container);
    bool takeOwnership @group(fields) @editable @hint("Whether the array should own the objects inserted into it");
    cOwnedObject *contents[] @getter(get) @sizeGetter(size) @hint("Objects contained in the array");
}

class cMessage extends cOwnedObject
{
    @icon("message");
    long id @group("message") @hint("Automatically assigned unique identifier");
    long treeId @group("message") @hint("Identifier shared between the message and its copies");
    short kind @group("message") @editable @hint("Generic user-settable attribute, usually carries \"type\" or \"role\" or \"category\" of message");
    short schedulingPriority @group("message") @editable @hint("Controls order of messages with equal timestamps in FES");
    string displayString @group("message") @hint("Controls appearance of the message in GUI");
    cObject *controlInfo @hint("Used with protocol stacks: carries extra information when a packet is sent between protocol layers");
    cArray parList @group("message") @hint("OBSOLETE: use of \"parList\" should be replaced with message subclassing in the few models that still use it");

    bool isScheduled @getter(isScheduled) @group(sending) @hint("Whether message is currently scheduled/in transit or not");
    bool isSelfMessage @getter(isSelfMessage) @group(sending) @hint("Whether message is a self-message, scheduled to be delivered back to the same module at a later time");
    simtime_t creationTime @group(sending) @hint("Simulation time the message was created");
    simtime_t sendingTime @group(sending) @hint("Simulation time of the current or last sending/scheduling of the message");
    simtime_t arrivalTime @group(sending) @hint("Simulation time the message will be/was delivered to the destination module");
    simtime_t timestamp @group(sending) @editable @hint("User-settable timestamp for generic use");

    int senderModuleId @group(sending) @hint("ID of the module performing the current or last send/schedule operation");
    int senderGateId @group(sending) @hint("Module-local ID of the gate on which the message was sent out -- -1==none for self-messages and after \"sendDirect\"");
    cModule *senderModule @group(sending) @hint("ID of the module performing the current or last send/schedule operation") @eventlog(fullPath);
    cGate *senderGate @group(sending) @hint("The gate on which the message was sent out -- NULL for self-messages and after \"sendDirect\"") @eventlog(fullName);

    int arrivalModuleId @group(sending) @hint("ID of the arrival module of the current or last sending/scheduling");
    int arrivalGateId @group(sending) @hint("Module-local ID of arrival gate for current or last sending -- -1==none for self-messages");
    cModule *arrivalModule @group(sending) @hint("Arrival module for current or last sending/scheduling") @eventlog(fullPath);
    cGate *arrivalGate @group(sending) @hint("Arrival gate for current or last sending -- NULL for self-messages") @eventlog(fullName);

    //XXX various IDs
}

class cPacket extends cMessage
{
    @icon("packet");
    int64 bitLength @group("packet") @editable @hint("Simulated length of the message in bits, affects transmission time and probability of bit errors when sent through a channel");
    int64 byteLength @group("packet") @editable @hint("Length in bytes, i.e. length in bits divided by eight");
    bool hasBitError @getter(hasBitError) @group("packet") @setter(setBitError) @editable @hint("Indicates that a bit error occurred when the message was sent through a channel with nonzero bit error rate");
    cPacket *encapsulatedPacket @hint("Used with protocol stacks: stores an encapsulated higher-layer packet");
    bool isReceptionStart @getter(isReceptionStart) @group(sending) @hint("When duration is nonzero: whether this message represents the start or the end of the frame reception");
    simtime_t duration @group(sending) @hint("Transmission time over a channel with datarate");
}

//----

class cStatistic extends cOwnedObject
{
    @icon(statistic);
    long count @hint("Number of observations collected so far");
    double weights @hint("Sum of weights, which equals the number of observations in the unweighted case");
    double sum @hint("Sum of observations");
    double sqrSum @hint("Sum of squares of the observations");
    double min @hint("Minimum of the observations");
    double max @hint("Maximum of the observations");
    double mean @hint("Mean of the observations");
    double stddev @hint("Standard deviation of the observations");
    double variance @hint("Variance of the observations");
}

class cStdDev extends cStatistic
{
}

class cWeightedStdDev extends cStdDev
{
}

class cDensityEstBase extends cStdDev
{
    bool isTransformed @getter(isTransformed) @group(histogram) @hint("If false, the object is still collecting initial observations to be used for laying out histogram cells");
    unsigned long underflowCell @group(histogram) @hint("Number of observations below the first histogram cell");
    unsigned long overflowCell @group(histogram) @hint("Number of observations above the last histogram cell");
    int numCells @group(histogram) @hint("Number of cells in the histogram");
    cDensityEstBase_Cell cellInfo[] @getter(internalGetCellInfo) @sizeGetter(getNumCells) @group(histogram) @hint("Histogram cell bounds, observation count in the cell, and density estimate in the cell");
}

class cHistogramBase extends cDensityEstBase
{
}

class cHistogram extends cHistogramBase
{
}

class cVarHistogram extends cHistogramBase
{
}

class cLongHistogram extends cHistogram
{
}

class cDoubleHistogram extends cHistogram
{
}

class cKSplit extends cDensityEstBase
{
}

class cPSquare extends cDensityEstBase
{
}

class cTransientDetection extends cOwnedObject
{
}

class cAccuracyDetection extends cOwnedObject
{
}

class cTDExpandingWindows extends cTransientDetection
{
}

class cADByStddev extends cAccuracyDetection
{
}

//----

class cExpression extends cObject
{
    string str @getter(str);
}

class cFSM extends cOwnedObject
{
    int state @hint("Numeric code of the state the FSM is currently in");
    string stateName @hint("Name of the current FSM state");
}

class cNEDMathFunction extends cNoncopyableOwnedObject
{
    string category @hint("Function category");
    string description;
    int numArgs @hint("Number of \"double\" parameters this function takes");
}

class cNEDFunction extends cNoncopyableOwnedObject
{
    string signature @hint("Argument types and return value");
    string category @hint("Function category");
    string description;
    char returnType;
    char argType[] @sizeGetter(getMaxArgs);
    int minArgs @hint("Number of mandatory arguments");
    int maxArgs @hint("Maximum number of arguments");
}

class cOutVector extends cNoncopyableOwnedObject
{
    @icon(outvector);
    bool isEnabled @getter(isEnabled) @setter(setEnabled) @editable @hint("If disabled, values passed to this object to record are simply discarded");
    long valuesReceived @hint("Number of values passed to this object to record");
    long valuesStored @hint("Number of values actually stored on the disk");
}

class cPar extends cObject
{
    @icon(param);
    string value @getter(str) @setter(parse) @editable;
    char type @enum(cPar_Type) @hint("Parameter type");
    string unit @hint("For long and double types only");
    bool isNumeric @getter(isNumeric) @group(flags) @hint("Whether parameter type is numeric, i.e. double or long");
    bool isVolatile @getter(isVolatile) @group(flags) @hint("Whether parameter was declared volatile in the NED file");
    bool isExpression @getter(isExpression)@group(flags) @hint("Whether parameter value is a constant or an expression");
    bool isShared @getter(isShared) @group(flags) @hint("Whether storage could be optimized by several modules sharing the same parameter value object");
}

class cMsgPar extends cOwnedObject
{
    string value @getter(str) @setter(parse) @editable @hint("Parameter value");
    char type @enum(cPar_Type) @hint("Parameter type");
    bool isNumeric @getter(isNumeric) @group(flags) @hint("Whether parameter is of numeric type");
    bool isConstant @getter(isConstant) @group(flags) @hint("Whether the parameter has a constant value");
}

class cLinkedList extends cOwnedObject
{
    @icon(queue);
    int length @hint("Number of items contained");
}

class cMessageHeap extends cOwnedObject
{
    @icon(container);
    int length @hint("Number of items contained");
    cMessage *messages[] @getter(peek) @sizeGetter(getLength) @hint("Self-messages currently scheduled and messages currently in transit");
}

class cQueue extends cOwnedObject
{
    @icon(queue);
    bool takeOwnership @group(fields) @editable @hint("Whether the queue should own the objects inserted into it");
    int length @hint("Number of items in the queue");
    cOwnedObject *contents[] @getter(get) @sizeGetter(getLength) @hint("Queue contents");
}

class cPacketQueue extends cQueue
{
    int64 bitLength @hint("Total size of messages in the queue");
    int64 byteLength @hint("Total size of messages in the queue, in bytes");
}

class cHasher extends void
{
   string hash @getter(str) @hint("The current hash value");
}

class cSimulation extends cNoncopyableOwnedObject
{
    @icon(container);
    simtime_t simTime @hint("The current simulation time in seconds");
    int64 eventNumber @hint("The current event number -- counts from 0 up");
    cMessageHeap messageQueue @label(futureEvents) @hint("Self-messages scheduled, and messages in transit");
    int lastModuleId @group(modules) @hint("The largest module ID issued so far");
    cModule *systemModule @group(modules) @hint("The top-level module");
    cModule *module[] @sizeGetter(getLastModuleId) @group(modules) @label(modules) @hint("List of modules, indexed with module ID");
    cHasher *hasher @hint("Used for fingerprint calculation");
}

class cScheduler extends cObject
{
}

class cSequentialScheduler extends cScheduler
{
}

class cRealTimeScheduler extends cScheduler
{
}

cplusplus {{
typedef cTopology::Node cTopology_Node;
typedef cTopology::Link cTopology_Link;
typedef cTopology::LinkIn cTopology_LinkIn;
typedef cTopology::LinkOut cTopology_LinkOut;
}}

class cTopology_Link extends void;
class cTopology_LinkIn extends cTopology_Link;
class cTopology_LinkOut extends cTopology_Link;

class cTopology_Node extends void
{
    int moduleId @hint("ID of the module this node corresponds to");
    cModule *module @hint("The module this node corresponds to");
    double weight @hint("Node weight -- affects graph algorithms such as shortest path");
    bool enabled @getter(isEnabled) @hint("Node state -- affects graph algorithms such as shortest path");

    cTopology_LinkIn *inLink[] @getter(getLinkIn) @sizeGetter(getNumInLinks) @hint("Incoming links of this graph node");
    cTopology_LinkIn *outLink[] @getter(getLinkOut) @sizeGetter(getNumOutLinks) @hint("Outgoing links of this graph node");

    double distanceToTarget @group(shortest path) @hint("After running a shortest path algorithm: distance to the target node");
    cTopology_LinkOut *path[] @sizeGetter(getNumPaths) @group(shortest path) @hint("The next link of the shortest path or paths towards the target node");
}

class cTopology_Link extends void
{
    double weight @hint("Link weight -- affects graph algorithms such as shortest path");
    bool enabled @getter(isEnabled) @hint("Link state -- affects graph algorithms such as shortest path");
}

class cTopology_LinkIn extends cTopology_Link
{
    cTopology_Node *remoteNode @hint("The node at the remote end of this connection");
    cGate *remoteGate @hint("The gate at the remote end of this connection");
    cGate *localGate @hint("The gate at the local end of this connection");
}

class cTopology_LinkOut extends cTopology_Link
{
    cTopology_Node *remoteNode @hint("The node at the remote end of this connection");
    cGate *remoteGate @hint("The gate at the remote end of this connection");
    cGate *localGate @hint("The gate at the local end of this connection");
}

class cTopology extends cOwnedObject
{
    int numNodes @group(fields) @hint("Number of nodes in this topology object");
    cTopology_Node *node[] @sizeGetter(getNumNodes) @hint("List of nodes in this topology object");
}

class cXMLElement
{
    string tagName @hint("XML element tag");
    string nodeValue @hint("Contents of text node inside this XML element");
    string sourceLocation @hint("Location this XML element was parsed from");
    bool hasAttributes @getter(hasAttributes) @hint("Whether this XML element has attributes");
    bool hasChildren @getter(hasChildren) @hint("Whether this XML element has child elements");
    string detailedInfo @getter(detailedInfo) @label(contents);
}

class cFigure extends cOwnedObject
{
    int id;
    bool visible @getter(isVisible);
    string tags;
    Point childOrigin @opaque;
    cFigure *children[] @getter(getFigure) @sizeGetter(getNumFigures);
}

class cGroupFigure extends cFigure
{
    Point location;
}

class cAbstractLineFigure extends cFigure
{
    Color lineColor;
    int lineStyle @enum(cFigure_LineStyle);
    double lineWidth;
    int capStyle @enum(cFigure_CapStyle);
    int startArrowHead @enum(cFigure_ArrowHead);
    int endArrowHead @enum(cFigure_ArrowHead);
}

class cLineFigure extends cAbstractLineFigure
{
    Point start;
    Point end;
}

class cArcFigure extends cAbstractLineFigure
{
    Rectangle bounds;
    double startAngle;
    double endAngle;
}

class cPolylineFigure extends cAbstractLineFigure
{
    Point points[] @getter(getPoint) @sizeGetter(getNumPoints);
    bool smooth;
    int joinStyle @enum(cFigure_JoinStyle);
}

class cAbstractShapeFigure extends cFigure
{
    bool outlined @getter(isOutlined);
    bool filled @getter(isFilled);
    Color lineColor;
    Color fillColor;
    int lineStyle @enum(cFigure_LineStyle);
    double lineWidth;
}

class cRectangleFigure extends cAbstractShapeFigure
{
    Rectangle bounds;
}

class cOvalFigure extends cAbstractShapeFigure
{
    Rectangle bounds;
}

class cPieSliceFigure extends cAbstractShapeFigure
{
    Rectangle bounds;
    double startAngle;
    double endAngle;
}

class cPolygonFigure extends cAbstractShapeFigure
{
    Point points[] @getter(getPoint) @sizeGetter(getNumPoints);
    bool smooth;
    int joinStyle @enum(cFigure_JoinStyle);
}

class cTextFigure extends cFigure
{
    Point location;
    Color color;
    Font font;
    string text;
    int anchor @enum(cFigure_Anchor);
    int alignment @enum(cFigure_Alignment);
}

class cImageFigure extends cFigure
{
    Point location;
    string imageName;
    Color tint;
    int anchor @enum(cFigure_Anchor);
}

class cCanvas extends cOwnedObject
{
    cFigure *rootFigure;
    string allTags;
}


cplusplus
{{

NAMESPACE_END

}}
