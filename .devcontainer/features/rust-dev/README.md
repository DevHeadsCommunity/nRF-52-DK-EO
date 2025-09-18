# Rust Development (rust-dev)

Rust Development Environment for Embedded Systems

## Example Usage

```json
"features": {
    "ghcr.io/DojoFive/embedops-features/rust-dev:0": {}
}
```

## Options

| Options Id | Description | Type | Default Value |
|-----|-----|-----|-----|
| rust-version | Rust version to install (stable, beta, nightly, or specific version like 1.75.0) | string | stable |
| target-triples | Comma-separated list of Rust target triples to install | string | thumbv7em-none-eabihf,thumbv8m.main-none-eabihf |

## Common Target Triples for Embedded Development

- `thumbv6m-none-eabi` - Cortex-M0, M0+
- `thumbv7m-none-eabi` - Cortex-M3
- `thumbv7em-none-eabi` - Cortex-M4, M7 without FPU
- `thumbv7em-none-eabihf` - Cortex-M4F, M7F with FPU
- `thumbv8m.base-none-eabi` - Cortex-M23
- `thumbv8m.main-none-eabi` - Cortex-M33, M35P without FPU
- `thumbv8m.main-none-eabihf` - Cortex-M33F, M35PF with FPU

---

_Note: This file was auto-generated from the [devcontainer-feature.json](https://github.com/DojoFive/embedops-features/blob/main/src/rust-dev/devcontainer-feature.json).  Add additional notes to a `NOTES.md`._
