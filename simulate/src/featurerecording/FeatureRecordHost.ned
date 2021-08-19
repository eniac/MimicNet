package approx.featurerecording;

import inet.nodes.inet.StandardHost;

module FeatureRecordHost extends StandardHost {
    parameters:
        int numFeatureRecorders = default(0); // no of FeatureRecorders.

    submodules:
        featureRecorder[numFeatureRecorders]: FeatureRecorder {
            @display("p=53,338,r,10");
        }
}
