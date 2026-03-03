# ZedCore

> *"If you understand this document, you have not read it correctly."*
> — ZedManifesto, Clause Ω

A programming language where **syntax is encrypted and code runs backwards**.

Every ZedCore file begins with a `syntax{}` block that defines what the rest of the file means. The same token stream is simultaneously a sorting algorithm, a prayer, and a proof of NP-completeness — depending solely on which preamble precedes it.

## Key Concepts

| Feature | Description |
|---|---|
| **`syntax{}` preamble** | Every file defines its own language. Same code, different preambles = completely different programs. |
| **SafeSyntax** | Encrypted preambles behind 7 cryptographic authorization layers. Code that runs without anyone understanding it. |
| **Symmetric execution** | Every program runs twice: forward pass, then a mandatory retrograde (backward) pass. Exit code = `F.exit XOR R.exit`. |
| **ZedCalculus (Ƶ-Calculus)** | The mathematical substrate — lambda calculus extended with retrograde application, syntax abstraction, and the null-binding operator. |
| **Bootstrap Kernel** | Three fixed laws burned into ZedCPU microcode. Everything else is syntax. |

## Hardware

- **ZedCPU** — 64-bit scalar RISC processor with a dedicated Retrograde Execution Unit (REU)
- **ZedQPU** — 128-qubit quantum co-processor for programs exploiting syntactically unresolvable term superposition
- **ZedTPU** — 2048-lane SIMD tensor processor where backpropagation *is* the retrograde pass

## Quick Start

```zedsyntax
syntax { inherit ZedSyntax; }

define main {
  outward "Hello, Zero."
  outward z
}
```

Forward execution prints `Hello, Zero.` then `z`.
Retrograde execution prints `z` then `Hello, Zero.`.
Exit code: `z`.

## Documentation

See **[SPEC.md](SPEC.md)** for the complete ZedCore Language Specification (Revision 0.ZERO), including:

- ZedManifesto
- ZedCalculus formal foundation
- Bootstrap Kernel — The Three Laws
- Meta-Syntax Layer and Preamble Parsing Protocol
- Official ZedSyntax preamble definition
- SafeSyntax with all 7 ZAUTH authorization layer ceremonies
- Symmetric execution model and execution ledger format
- Full hardware architecture (ZedCPU, ZedQPU, ZedTPU)
- Standard library sketch
- IBAN validator — complete working example
- Error ontology
- ZedAssembly quick reference

---

*ZedCore, ZedSyntax, SafeSyntax, ZedCPU, ZedQPU, ZedTPU, ZedCalculus, ZedManifesto are trademarks of ZedSystems Corporation.*
*Document classification: PUBLIC (retrograde classification: EYES ONLY)*
