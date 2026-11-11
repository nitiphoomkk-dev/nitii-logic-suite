# Build Nitii Logic Suite 3.0.0

From the repository root, download the full v1.2.0 ZIP and the v1.2.1 auto-update patch from [GitHub Releases](https://github.com/nitiphoomkk-dev/nitii-logic-suite/releases). The builder verifies their pinned SHA-256 digests and includes install_nitii.py and both Thai guides from this directory.

```sh
python distribution/v3/build_suite.py --base Nitii_Logic_Suite_1.2.0.zip --patch Nitii_Auto_Update_Patch_1.2.1.zip --out dist
```

Published archive SHA-256: `46b9111914f478e82ecd2a891d2760045c4f70c5540f7252676475227de5ff22`.
