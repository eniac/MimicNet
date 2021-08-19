import inet.linklayer.queue.FIFOQueue;
import inet.linklayer.queue.REDDropper;
import inet.linklayer.IOutputQueue;

module REDQueue like IOutputQueue
{
    gates:
        input in;
        output out;

    submodules:
        red: REDDropper;
        fifo: FIFOQueue;
    connections:
        in --> red.in[0];
        red.out[0] --> fifo.in++;
        fifo.out --> out;
}

