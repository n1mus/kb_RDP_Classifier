This directory contains any reference data required for this module to run that is not already present in KBase.

For any reference data that is too large to host on Github (greater than 100MB), follow the [Reference Data Guide](https://kbase.github.io/kb_sdk_docs/howtos/work_with_reference_data.html) for an alternative.

Except for now, it has been hacked with `split` and `cat`, i.e.,

split -b 99M SILVA_138_SSU_NR_99.tgz SILVA_138_SSU_NR_99_
cat SILVA_138_SSU_NR_99_* > SILVA_138_SSU_NR_99.tgz
