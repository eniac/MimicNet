import ned.DatarateChannel;

channel NormalChannel extends DatarateChannel
{   
    int linkSpeed @unit(Mbps) = default(100Mbps);
    delay = 500us;
    datarate = linkSpeed;
}

channel IdealChannel extends DatarateChannel
{
    int linkSpeed @unit(Mbps) = default(100Mbps);
    delay = 0us;
    datarate = linkSpeed;
}

