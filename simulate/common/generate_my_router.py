import sys

routing = sys.argv[1]
print(routing)

if routing == "ecmp":
    s1 = "ecmp.ECMPRoutingTable"
    s2 = "ECMPRoutingTable"
    s3 = ""
else:
    print("Router configuration not supported")
    sys.exit(1)

outfname = "out/MyRouter.ned"
with open(outfname, "w") as outf:
    outf.write(
        """import approx.ipv4flow.FlowRouter;
import approx.ipv4flow.{s1};

module MyRouter extends FlowRouter
{{
    parameters:
        int SEED=default(123);
    submodules:
        routingTable: {s2} {{
            parameters:
                @display("p=53,225;is=s");
                IPForward = IPForward;
                forwardMulticast = forwardMulticast;
                routingFile = routingFile;
                seed = SEED;
                {s3}
        }}
}}""".format(s1=s1, s2=s2, s3=s3)
        )
