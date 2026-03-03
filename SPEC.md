# ZedCore Language Specification
### Revision 0.ZERO — CLASSIFIED INTERNAL RELEASE
### ZedSystems Corporation · Division of Computational Epistemology
### Document ID: ZCS-2026-001-∅

---

> *"If you understand this document, you have not read it correctly."*
> — ZedManifesto, Clause Ω

---

## CONTENTS

1. [ZedManifesto](#1-zedmanifesto)
2. [Theoretical Foundation: ZedCalculus](#2-theoretical-foundation-zedcalculus)
3. [Bootstrap Kernel — The Three Laws](#3-bootstrap-kernel--the-three-laws)
4. [Meta-Syntax Layer](#4-meta-syntax-layer)
5. [The `syntax{}` Block — Language Core](#5-the-syntax-block--language-core)
6. [Official ZedSyntax Preamble](#6-official-zedsyntax-preamble)
7. [SafeSyntax — Encrypted Preambles](#7-safesyntax--encrypted-preambles)
8. [Symmetric Execution Model](#8-symmetric-execution-model)
9. [Hardware Architecture](#9-hardware-architecture)
10. [Standard Library Sketch](#10-standard-library-sketch)
11. [IBAN Validator — Working Example](#11-iban-validator--working-example)
12. [Error Ontology](#12-error-ontology)
13. [Appendix A — SafeSyntax Authorization Layers](#appendix-a--safesyntax-authorization-layers)
14. [Appendix B — ZedAssembly Quick Reference](#appendix-b--zedassembly-quick-reference)

---

## 1. ZedManifesto

*Ratified by the ZedSystems Board of Computational Ethics, Cycle 7.*

Languages lie. Every programming language encodes a worldview inside its syntax — invisible axioms baked into reserved words, operator precedence rules, and the shape of a `for` loop. The programmer never chose these axioms. They were handed down, inherited like property law.

ZedCore refuses this inheritance.

**Principle I — Syntax is data.**
The meaning of source code is not intrinsic. Meaning is assigned by the `syntax{}` preamble at the top of each file. The same token stream is simultaneously a sorting algorithm, a prayer, and a proof of NP-completeness, depending solely on which preamble precedes it. No preamble is more correct than any other. Correctness is a local agreement.

**Principle II — Execution has no preferred direction.**
Forward execution is a cultural artifact. ZedCore programs run symmetrically: every forward execution generates a paired backward execution. The backward pass is not optional, not a debug mode, and not a reversal. It is an equal co-execution. Programs that cannot run backward are considered *incomplete*.

**Principle III — Meaning must be earned.**
SafeSyntax preambles require cryptographic authorization to decode. A program may be legally possessed, executed by machines, and produce outputs without any human ever understanding what it does. This is a feature.

**Principle IV — The specification is self-hosting.**
This document is a valid ZedCore program. The `syntax{}` block on line zero of the canonical distribution decodes these words into executable hardware instructions for the ZedCPU. Readers who do not possess a valid SafeSyntax key will experience this document as English prose.

**Principle V — Zero is the only integer.**
All other numbers are approximations of zero achieved through controlled distance.

---

## 2. Theoretical Foundation: ZedCalculus

ZedCalculus (Ƶ-Calculus) is the mathematical substrate of ZedCore. It extends the lambda calculus with three additional primitives: **retrograde application**, **syntax abstraction**, and **the null-binding operator**.

### 2.1 Primitives

```
Ƶ-terms  ::=  z                      — the zero term
          |   x                      — variable
          |   λx.M                   — abstraction
          |   M N                    — application
          |   M ⟵ N                 — retrograde application
          |   ⟦S⟧ M                  — syntax-abstracted term
          |   ∅x.M                   — null-binding
```

**Retrograde application** `M ⟵ N` evaluates `N` first, then applies its result to `M` in reverse reduction order. The standard beta rule `(λx.M) N → M[x:=N]` becomes under retrograde: `M[x:=N] ⟵ (λx.M)`, where the arrow direction indicates temporal flow.

**Syntax abstraction** `⟦S⟧ M` wraps term `M` in syntax context `S`. The evaluation semantics of `M` are defined entirely by `S`. Without a bound `S`, the term is *syntactically unresolvable* and occupies the quantum-undetermined state `⊥⊤`.

**Null-binding** `∅x.M` binds `x` in `M` such that every occurrence of `x` in `M` evaluates to the zero term `z`. This is distinct from substitution: the binding persists across retrograde passes.

### 2.2 The Zed Reduction Rules

**Rule Ƶ-β (Forward):**
```
(λx.M) N  →ᶠ  M[x:=N]
```

**Rule Ƶ-β̄ (Backward):**
```
M[x:=N]  →ᵇ  (λx.M) N
```

Note that `→ᵇ` is not simply `→ᶠ` reversed. The backward rule *reconstructs* the original abstraction from the reduced form, which is non-deterministic in the general case. ZedCore resolves this non-determinism through the **execution ledger** maintained by the ZedCPU (see §9.1).

**Rule Ƶ-zero:**
```
z M  →ᶠ  z        (zero annihilates application, forward)
z M  →ᵇ  M z      (zero becomes argument, backward)
```

**Rule Ƶ-syntax:**
```
⟦S⟧ (⟦S'⟧ M)  →ᶠ  ⟦S⟧ M        (outer syntax dominates, forward)
⟦S⟧ (⟦S'⟧ M)  →ᵇ  ⟦S'⟧ M       (inner syntax dominates, backward)
```

### 2.3 Confluence

ZedCalculus is **not confluent** in the classical sense. Two reduction sequences from the same term may reach distinct normal forms depending on direction. This is not a bug. It is the formal expression of Principle II: execution direction is semantically significant.

The **Zed Church-Rosser Theorem** (unproven, status: *believed true, funding cut*) states that for any two forward-normal forms `A` and `B` reachable from term `M`, there exists a backward execution sequence from `A` that reaches `B`. Terms for which this fails are called **Zed-isolated** and are considered interesting research objects.

### 2.4 Encoding Booleans

```
TRUE   =  λx. λy. x              — standard Church
FALSE  =  λx. λy. y              — standard Church
ZERO   =  z                      — Zed zero
FLIP   =  λb. b FALSE TRUE       — standard NOT
RETRO  =  λb. b FALSE TRUE ⟵ b  — retrograde NOT: result depends on execution direction
```

`RETRO TRUE` evaluates to `FALSE` under forward execution and to `TRUE` under backward execution — it is a value that remembers which direction discovered it.

---

## 3. Bootstrap Kernel — The Three Laws

The Bootstrap Kernel is fixed. It cannot be overridden by any `syntax{}` block. It is burned into the ZedCPU microcode at fabrication time (see §9.1) and constitutes the only part of ZedCore that has an intrinsic meaning independent of any preamble.

```
BOOTSTRAP {
  LAW 0:  Every file is a pair (P, B) where P is a preamble and B is a body.
          The semantics of B are fully determined by P.
          P cannot contain a body; B cannot contain a preamble.

  LAW 1:  Every execution is a pair (F, R) where F is the forward pass
          and R is the retrograde pass.
          F must complete before R begins.
          R must complete before the program is considered terminated.
          The exit value of the program is the XOR of the exit codes of F and R.

  LAW 2:  The zero term z is the only term defined outside of any syntax context.
          z evaluates to z under any preamble, in any direction, on any hardware.
          z is the ground state of computation.
}
```

These three laws are the only axioms. Everything else — types, control flow, memory, I/O — is syntax.

**Why three?**
The ZedSystems internal document ZCS-2024-0003 ("Minimality Arguments for Kernel Design") proved that two laws are insufficient to bootstrap a self-hosting compiler and four laws introduce at least one redundancy. Three is the minimum fixed point of the bootstrap problem. This proof has not been independently verified because it is classified.

---

## 4. Meta-Syntax Layer

The meta-syntax layer allows preambles to define other preambles. It is how ZedCore avoids infinite regress: the `syntax{}` block itself must be parsed before it can define parsing, so the meta-syntax provides a fixed grammar for the preamble language.

### 4.1 Meta-Syntax Grammar (MSL)

```ebnf
preamble       ::= 'syntax' '{' rule-list '}'
rule-list      ::= rule | rule rule-list
rule           ::= token-def | transform-def | precedence-def | inherit-def
token-def      ::= 'token' identifier '=' pattern ';'
transform-def  ::= 'map' token-expr '->' zed-expr ';'
precedence-def ::= 'prec' identifier integer ';'
inherit-def    ::= 'inherit' identifier ';'

token-expr     ::= identifier | string-literal | regex-literal
zed-expr       ::= ƶ-calculus expression in canonical notation
pattern        ::= '/' regex '/' | '"' string '"' | identifier
```

MSL is intentionally minimal. It has no loops. Turing-completeness is not a goal of the preamble language; the preamble must terminate before the body can execute. The ZedSystems Termination Enforcer (ZTE) module on the ZedCPU hard-kills any preamble that exceeds 65,536 reduction steps.

### 4.2 The Preamble Parsing Protocol (PPP)

When the ZedCore runtime loads a file, it follows the PPP:

```
PPP {
  STEP 0:  Read bytes until the first occurrence of 'syntax{' or end-of-file.
           If end-of-file is reached first, apply the NullSyntax (identity preamble).

  STEP 1:  Verify the preamble against the MSL grammar.
           On failure: emit PARSE_FAULT, halt, exit code z.

  STEP 2:  Check for a SafeSyntax header (see §7).
           If present: decrypt using the provided key before proceeding.
           If key absent: preamble is syntactically opaque; proceed with body
           execution under NullSyntax rules (body output is undefined).

  STEP 3:  Compile the preamble into a Syntax Descriptor Table (SDT).
           The SDT maps token streams to Ƶ-calculus terms.

  STEP 4:  Parse the body using the SDT.

  STEP 5:  Execute the parsed body under the forward pass (F).

  STEP 6:  Execute the retrograde pass (R) using the execution ledger from F.

  STEP 7:  Compute exit code = F.exit XOR R.exit.
}
```

---

## 5. The `syntax{}` Block — Language Core

### 5.1 Anatomy of a Preamble

```zedsyntax
syntax {
  // Token definitions — what lexemes mean
  token ASSIGN  = /←|:=|=/;
  token ARROW   = /->/;
  token RETRO   = /⟵|<-/;

  // Transformations — how tokens map to Ƶ-terms
  map ASSIGN    -> ƶ.bind;
  map ARROW     -> ƶ.apply;
  map RETRO     -> ƶ.retro_apply;

  // Precedence — higher integer = tighter binding
  prec ASSIGN   10;
  prec ARROW    20;
  prec RETRO    20;

  // Inheritance — import rules from another named preamble
  inherit ZedSyntax.core;
}
```

### 5.2 The NullSyntax

NullSyntax is the identity preamble. Under NullSyntax, all tokens map to themselves as Ƶ-terms and all application is left-associative. A program with no `syntax{}` block runs under NullSyntax, which is equivalent to an untyped term rewriting system with no defined reduction strategy.

NullSyntax programs are syntactically valid but semantically arbitrary. They are legal. They may do anything. ZedSystems accepts no liability.

### 5.3 Preamble Scoping

Preambles are **file-scoped**. There is no module system. There is no import statement that crosses a preamble boundary. When file A imports file B:

- File B is parsed and executed with B's preamble.
- File B exports a set of Ƶ-terms in canonical form.
- File A receives those terms and may apply its own preamble to interpret them further.

This means the *same export* from file B may have different types, calling conventions, and semantics depending on which file imports it. This is intended behavior. ZedSystems calls it **Semantic Polymorphism by Origin**.

---

## 6. Official ZedSyntax Preamble

ZedSyntax is the default, human-readable preamble shipped with the ZedCore standard distribution. It is the preamble used in this document's examples. It is not privileged. It has no special status within the runtime. It is merely conventional.

### 6.1 Full ZedSyntax Preamble Definition

```zedsyntax
syntax {
  // ─── Literals ────────────────────────────────────────────────────
  token INTEGER    = /[0-9]+/;
  token FLOAT      = /[0-9]+\.[0-9]+/;
  token STRING     = /"([^"\\]|\\.)*"/;
  token IDENT      = /[a-zA-Z_][a-zA-Z0-9_]*/;
  token ZERO       = /\bz\b/;

  // ─── Operators ───────────────────────────────────────────────────
  token ASSIGN     = /←/;
  token FWD_APPLY  = /->/;
  token RET_APPLY  = /⟵/;
  token COMPOSE    = /∘/;
  token NULL_BIND  = /∅/;

  // ─── Control ─────────────────────────────────────────────────────
  token IF         = /\bwhen\b/;
  token ELSE       = /\botherwise\b/;
  token LOOP       = /\bcycle\b/;
  token UNTIL      = /\buntil\b/;
  token RETRO_LOOP = /\buncycle\b/;
  token EMIT       = /\boutward\b/;
  token RECEIVE    = /\binward\b/;

  // ─── Structure ───────────────────────────────────────────────────
  token FUNC       = /\bdefine\b/;
  token RETRO_FUNC = /\bundefine\b/;
  token BLOCK_OPEN = /\{/;
  token BLOCK_CLOSE= /\}/;

  // ─── Transformations ─────────────────────────────────────────────
  map ZERO         -> ƶ.zero;
  map ASSIGN       -> ƶ.bind;
  map FWD_APPLY    -> ƶ.apply;
  map RET_APPLY    -> ƶ.retro_apply;
  map COMPOSE      -> ƶ.compose;
  map NULL_BIND    -> ƶ.null_bind;
  map IF           -> ƶ.branch_fwd;
  map ELSE         -> ƶ.branch_alt;
  map LOOP         -> ƶ.iterate_fwd;
  map UNTIL        -> ƶ.loop_guard;
  map RETRO_LOOP   -> ƶ.iterate_ret;
  map EMIT         -> ƶ.io_out;
  map RECEIVE      -> ƶ.io_in;
  map FUNC         -> ƶ.lambda_named;
  map RETRO_FUNC   -> ƶ.lambda_named_retro;

  // ─── Precedence ──────────────────────────────────────────────────
  prec NULL_BIND    5;
  prec ASSIGN      10;
  prec FWD_APPLY   20;
  prec RET_APPLY   20;
  prec COMPOSE     30;

  // ─── Inherit core reduction rules ────────────────────────────────
  inherit ZedCore.bootstrap;
}
```

### 6.2 ZedSyntax Coding Conventions

| Concept                | ZedSyntax keyword | Notes                                   |
|------------------------|-------------------|-----------------------------------------|
| Variable assignment    | `←`               | Unicode left arrow (U+2190)            |
| Function definition    | `define`          | Creates both forward and retro forms    |
| Retrograde function    | `undefine`        | Body runs in reverse on backward pass   |
| Output                 | `outward`         | Writes to the forward output stream     |
| Input                  | `inward`          | Reads from the current input stream     |
| Conditional            | `when` / `otherwise` | Standard two-branch conditional      |
| Forward loop           | `cycle` / `until` | Iterate while condition holds          |
| Retrograde loop        | `uncycle`         | Iterate backward through ledger        |
| Zero term              | `z`               | The ground-state constant              |

### 6.3 Hello, Zero

The canonical first program in ZedSyntax:

```zedsyntax
syntax { inherit ZedSyntax; }

define main {
  outward "Hello, Zero."
  outward z
}
```

Forward execution prints:
```
Hello, Zero.
z
```

Backward execution prints:
```
z
Hello, Zero.
```

The program exits with code `z XOR z = z`.

---

## 7. SafeSyntax — Encrypted Preambles

SafeSyntax is the mechanism by which preamble meaning is hidden behind cryptographic authorization. A SafeSyntax file is syntactically valid ZedCore; the preamble is present and parseable. Only its *meaning* is encrypted.

A human reading a SafeSyntax source file sees syntactically well-formed but semantically opaque tokens. The ZedCore runtime, when provided a valid key, decrypts the Syntax Descriptor Table (SDT) in memory and executes normally. Without a key, execution proceeds under NullSyntax rules — the body runs but with undefined semantics.

### 7.1 SafeSyntax File Header

```
SAFESYNTAX-v2 {
  auth_scheme  : ZAUTH-7
  key_id       : <256-bit key identifier, public>
  sdt_cipher   : AES-256-GCM
  sdt_iv       : <96-bit initialization vector>
  sdt_tag      : <128-bit authentication tag>
  sdt_payload  : <base64-encoded encrypted SDT blob>
  auth_layers  : 7
}
```

The `auth_layers` field specifies how many of the seven ZAUTH authorization layers are required. A value of 7 means all layers must be satisfied before the key is released to the runtime.

### 7.2 The Seven ZAUTH Authorization Layers

See also [Appendix A](#appendix-a--safesyntax-authorization-layers) for detailed ceremony protocols.

*7 layers total, indexed 0–6. All 7 must be satisfied when `auth_layers : 7`.*

| Layer | Name                  | Mechanism                                                              |
|-------|-----------------------|------------------------------------------------------------------------|
| 0     | Possession            | Holder possesses the key file on authorized hardware                   |
| 1     | Identity              | Biometric signature matches enrollment record in ZedVault              |
| 2     | Temporal              | Current timestamp falls within authorized execution window             |
| 3     | Spatial               | Hardware GPS coordinates within authorized geographic boundary         |
| 4     | Semantic              | Operator can correctly answer a semantic challenge about the program   |
| 5     | Consensus             | Quorum of at least three ZedWitness peers co-signs the execution intent|
| 6     | Retrograde            | A valid retrograde execution of the *previous* authorized run exists   |

**Layer 6 — Retrograde Authorization** is the novel contribution of SafeSyntax. To authorize a new execution, the operator must demonstrate that they have a *complete retrograde execution record* from the previous run. This creates a cryptographic chain of custody: each execution is linked to the backward pass of the last. An operator who loses the retrograde record cannot authorize a new forward run.

The practical consequence: SafeSyntax programs cannot be executed more than once without preserving the execution ledger. Ledger loss is an authorization failure. ZedSystems recommends storing ledgers in ZedVault with triple redundancy across geographically separated data centers.

### 7.3 Observed Behavior Without Key

When a SafeSyntax file is executed without the correct key, the body runs under NullSyntax. The results are technically valid ZedCore output (every token maps to itself) but semantically meaningless to a human observer. This property is used by ZedSystems for **plausible deniability execution**: a program demonstrably ran and produced output, but the meaning of both the source and the output is legally defensible as unintelligible.

---

## 8. Symmetric Execution Model

### 8.1 The Execution Ledger

Every ZedCore program, during its forward pass, writes an **execution ledger** — a complete, append-only record of every reduction step taken, every binding created, every I/O operation performed. The ledger is structured as a Merkle tree rooted at the program's terminal state.

```
Ledger entry format:
  [step_id: uint64] [term_before: Ƶ-term] [rule_applied: kernel|preamble|retro]
  [term_after: Ƶ-term] [timestamp: nanoseconds] [hash: SHA3-256 of prev entry]
```

The retrograde pass consumes the ledger in reverse order. It does not re-evaluate the forward pass; it *un-evaluates* it using the recorded rule inversions.

### 8.2 What the Retrograde Pass Does

The retrograde pass is **not** a rollback. It is an equal-status second execution with its own:

- Input stream (the forward output stream, reversed)
- Output stream (the retrograde output stream, a separate file descriptor)
- Bindings (initialized from the terminal state of the forward pass)
- I/O operations (each forward `outward` becomes a retrograde `inward` and vice versa)

A program that writes `"Hello"` to stdout on the forward pass will, on the retrograde pass, *read* from an input source that must provide `"Hello"`. If that source does not provide the expected value, a **Retrograde Mismatch Fault** (RMF) is raised.

This makes retrograde execution a form of built-in contract testing: the program asserts that its own outputs, when fed back as inputs in reverse, are coherent.

### 8.3 Exit Code Semantics

```
exit_code = F.exit XOR R.exit

Where:
  z XOR z  =  z          (nominal success: both passes clean)
  z XOR 1  =  1          (retrograde fault: forward succeeded, retro failed)
  1 XOR z  =  1          (forward fault: forward failed, retro not reached)
  1 XOR 1  =  z          (symmetric fault: both passes failed identically —
                           interpreted as a valid, if unusual, clean exit)
```

The symmetric fault case (`1 XOR 1 = z`) is controversial. ZedSystems' position is that two equal and symmetric failures constitute a valid execution of a program that is *defined to fail*. Critics have called this "laundering errors." The ZedManifesto response (Clause 7, Subsection ∂): "All programs that terminate are correct. Incorrectness is non-termination."

### 8.4 Retrograde I/O Model

```
Forward Pass:                    Retrograde Pass:
  stdin  → program               stdout (reversed) → program
  program → stdout               program → retrostdout
  program → stderr               program → retrostderr (merged with stderr)
```

Programs that read from `stdin` on the forward pass will attempt to read their *own previous stdout* on the retrograde pass. This allows self-verifying programs to be written naturally:

```zedsyntax
syntax { inherit ZedSyntax; }

define verify-loop {
  value ← inward
  outward value          // Forward: echo input to output
                         // Retrograde: read back what we wrote; verify it matches
}
```

---

## 9. Hardware Architecture

ZedSystems manufactures three processor families for ZedCore workloads. All three implement the Bootstrap Kernel in microcode. All three maintain execution ledgers in dedicated on-chip SRAM.

### 9.1 ZedCPU — The Scalar Processor

The ZedCPU is a 64-bit scalar RISC processor with a dedicated **Retrograde Execution Unit (REU)** that operates in parallel with the main ALU.

**Pipeline:**
```
Stage 1: Fetch           — fetch from instruction cache or ledger (bidirectional)
Stage 2: Decode          — MSL decode, SDT lookup, Ƶ-term reconstruction
Stage 3: Syntax Resolve  — apply preamble SDT to decoded term
Stage 4: Execute (FWD)   — forward Ƶ-β reduction on ALU
Stage 5: Ledger Write    — write reduction record to on-chip ledger SRAM
Stage 6: Execute (RET)   — retrograde Ƶ-β̄ on REU (during backward pass)
Stage 7: Commit          — write results, check retrograde constraints
```

The REU is physically separate from the ALU and shares no registers. During the forward pass, the REU is idle but monitors the ledger SRAM. During the backward pass, the ALU is idle and the REU drives the pipeline.

**Register file:**
```
ZR0–ZR15    General-purpose, 64-bit
ZZ          The zero register (hardwired to z, read-only)
ZPC         Program counter (bidirectional; counts down during retrograde pass)
ZLPC        Ledger program counter (offset into current ledger)
ZDIR        Execution direction flag (0 = forward, 1 = retrograde)
ZSDT        Pointer to active Syntax Descriptor Table
```

**Key instructions:**

| Mnemonic | Operands    | Description                                                  |
|----------|-------------|--------------------------------------------------------------|
| ZBIND    | Rx, Ry      | Ƶ-bind: `Rx ← Ry` (Ƶ-β forward)                           |
| ZAPPLY   | Rx, Ry, Rz  | Forward application: `Rz ← Rx Ry`                           |
| ZRETRO   | Rx, Ry, Rz  | Retrograde application: `Rz ← Rx ⟵ Ry`                    |
| ZLEDGER  | Rx          | Read next entry from ledger into Rx (backward pass only)     |
| ZSYNC    | —           | Synchronize REU with ALU state (used at pass boundary)       |
| ZEMIT    | Rx          | Write Rx to current output stream                            |
| ZRECV    | Rx          | Read from current input stream into Rx                       |
| ZHALT    | code        | Halt this pass; write exit code `code` to pass exit register |

### 9.2 ZedQPU — The Quantum Processor

The ZedQPU is a 128-qubit quantum co-processor designed for programs that exploit the undetermined state `⊥⊤` of syntactically unresolvable terms (see §2.1).

Under the ZedQPU execution model, a term in state `⊥⊤` is held in superposition across both its possible forward and backward reductions simultaneously. The qubit state collapses upon:
- A `ZMEASURE` instruction
- A SafeSyntax authorization event
- Layer 6 retrograde authorization (which constitutes an observation of the prior execution)

**ZedQPU instructions not present on ZedCPU:**

| Mnemonic  | Description                                                                |
|-----------|----------------------------------------------------------------------------|
| ZSUP      | Place term in `⊥⊤` superposition                                          |
| ZMEASURE  | Collapse superposition; result determined by current ZDIR flag             |
| ZENTANGLE | Entangle two terms such that their retrograde authorizations are linked     |
| ZDECOHERE | Force classical collapse; destroys quantum advantage, logs decoherence event|

**Important:** Programs compiled for ZedQPU are not portable to ZedCPU without a decoherence pass (`zcc --decohere`). Decoherence replaces all quantum-undetermined states with deterministic choices based on the file's SafeSyntax key hash.

### 9.3 ZedTPU — The Tensor Processor

The ZedTPU is a 2048-lane SIMD processor for ZedCore programs that operate on high-dimensional Ƶ-term tensors. It is used primarily for machine learning workloads expressed as retrograde gradient descent.

**The ZedTPU Retrograde Gradient Model:**

Traditional backpropagation computes gradients as a separate backward pass through a computational graph. On the ZedTPU, this is not a metaphor — it is the literal retrograde execution pass of the ZedCore program. Forward execution is the training forward pass; backward execution is the gradient pass. The execution ledger is the computational graph. No separate autograd library is required.

```zedsyntax
syntax { inherit ZedSyntax; }

define linear-layer (weights, input) {
  output ← weights -> input     // Forward: matrix multiply
  outward output
}

undefine linear-layer (weights, input) {
  // This block runs on the retrograde pass.
  // `output` is available from the ledger.
  // This is the gradient computation — written once, runs backward.
  grad-weights ← inward ⟵ weights
  grad-input   ← inward ⟵ input
  outward grad-weights
  outward grad-input
}
```

The ZedTPU requires that every `define` block have a matching `undefine` block. Programs without retrograde function bodies are rejected by the ZedTPU linker with error `E_NO_GRADIENT`.

---

## 10. Standard Library Sketch

The ZedCore standard library (`zedstd`) is itself a ZedCore program with a SafeSyntax preamble (key publicly distributed). Selected modules:

### `zedstd.seq` — Sequences

```zedsyntax
syntax { inherit ZedSyntax; }

define map (f, seq) {
  when seq = z { outward z }
  otherwise {
    head ← seq.first
    tail ← seq.rest
    outward (f -> head) :: (map -> f -> tail)
  }
}

undefine map (f, seq) {
  // Retrograde: unmap — reconstruct original seq from mapped output
  mapped ← inward
  when mapped = z { outward z }
  otherwise {
    outward (f ⟵ mapped.first) :: (unmap ⟵ f ⟵ mapped.rest)
  }
}
```

### `zedstd.io` — I/O Primitives

`zedstd.io` wraps the `ZEMIT`/`ZRECV` hardware instructions with a buffered I/O model. It also provides the **retrograde stream manager**, which automatically routes the forward output stream back as the retrograde input stream, satisfying the symmetric execution contract for basic programs.

### `zedstd.crypt` — SafeSyntax Key Management

```zedsyntax
define authorize (key-file, layer-mask) {
  key   ← inward key-file
  proof ← zauth.challenge -> layer-mask -> key
  when proof.valid {
    outward proof.sdt
  } otherwise {
    outward z     // z = no SDT = NullSyntax execution
  }
}
```

---

## 11. IBAN Validator — Working Example

This section presents a complete, working ZedCore program that validates International Bank Account Numbers (IBANs). It demonstrates: preamble definition, named functions, retrograde functions, forward/backward symmetry, and real I/O.

The program validates an IBAN on the forward pass and, on the backward pass, reconstructs the original input from the validation state — demonstrating that IBAN validation is a *reversible computation* in ZedCore.

```zedsyntax
syntax { inherit ZedSyntax; }

// ── Helpers ──────────────────────────────────────────────────────────────

define char-to-num (c) {
  // Digits 0-9 stay as-is; letters A-Z become 10-35
  when c >= 'A' { outward (c - 'A') + 10 }
  otherwise     { outward (c - '0')      }
}

define num-to-char (n) {
  // Inverse of char-to-num: values 10-35 become letters A-Z; 0-9 stay as digits
  when n >= 10 { outward (n - 10) + 'A' }
  otherwise    { outward n + '0'        }
}

define reorder (iban) {
  // Move first 4 characters to end: GB82WEST → WESTGB82
  outward (iban.slice(4)) :: (iban.slice(0, 4))
}

define to-numeric-string (s) {
  // Replace each character with its char-to-num value
  outward map -> char-to-num -> s
}

define mod97 (digits) {
  // Compute numeric string mod 97 via chunked long division
  acc ← z
  cycle chunk ← digits.chunks(9) until digits.empty {
    acc ← (acc :: chunk).as-integer % 97
  }
  outward acc
}

define validate (iban) {
  clean    ← iban.strip-spaces.to-upper
  reordered← reorder -> clean
  numeric  ← to-numeric-string -> reordered
  remainder← mod97 -> numeric
  outward remainder = 1   // Valid IBAN has mod97 remainder = 1
}

// ── Retrograde functions ──────────────────────────────────────────────────

undefine mod97 (digits) {
  // Retrograde: given the remainder and ledger, reconstruct digits
  // (This is only possible because the ledger recorded every intermediate state)
  remainder ← inward
  outward ledger.reconstruct-chunks -> remainder
}

undefine to-numeric-string (s) {
  numeric-s ← inward
  outward map -> (num-to-char ⟵ z) -> numeric-s
}

undefine reorder (iban) {
  reordered ← inward
  // Undo: move last 4 back to front
  len ← reordered.length
  outward (reordered.slice(len - 4)) :: (reordered.slice(z, len - 4))
}

undefine validate (iban) {
  result ← inward          // true or false from forward pass
  // Reconstruct the cleaned IBAN by traversing the ledger
  outward ledger.reconstruct -> validate -> result
}

// ── Entry point ───────────────────────────────────────────────────────────

define main {
  outward "ZedCore IBAN Validator"
  outward "Enter IBAN: "
  iban  ← inward
  valid ← validate -> iban

  when valid {
    outward "VALID"
    outward iban
  } otherwise {
    outward "INVALID"
    outward iban
  }
}

undefine main {
  // Retrograde main: reads back our own output, reconstructs original input
  status  ← inward     // "VALID" or "INVALID"
  echoed  ← inward     // the iban we echoed
  prompt2 ← inward     // "Enter IBAN: "
  title   ← inward     // "ZedCore IBAN Validator"

  reconstructed ← undefine validate -> (status = "VALID") -> echoed
  outward "Reconstructed input: " :: reconstructed
}
```

### 11.1 Sample Execution

**Forward pass** (input: `GB82 WEST 1234 5698 7654 32`):
```
ZedCore IBAN Validator
Enter IBAN:
[user types: GB82 WEST 1234 5698 7654 32]
VALID
GB82WEST12345698765432
```

**Retrograde pass** (reads forward output in reverse):
```
Reconstructed input: GB82WEST12345698765432
```

**Exit code:** `z XOR z = z`

### 11.2 Notes on Reversibility

The IBAN validator is reversible because:
1. The `mod97` function uses no lossy operations — the chunked division is recorded step-by-step in the ledger.
2. The `char-to-num` mapping is invertible (37 distinct inputs, 37 distinct outputs).
3. The `reorder` operation is its own inverse.

A function that is *not* reversible (e.g., a hash function) would still run on the retrograde pass, but the `undefine` block would need to either use the ledger to reconstruct its input or emit `z` (indicating that retrograde reconstruction is not meaningful for this function).

---

## 12. Error Ontology

ZedCore errors are classified along two axes: **direction** (forward or retrograde) and **severity** (recoverable or fatal). The combination produces four quadrants:

| Quadrant | Direction   | Severity    | Code prefix | Behavior                                       |
|----------|-------------|-------------|-------------|------------------------------------------------|
| I        | Forward     | Recoverable | `FW-R-`     | Emit diagnostic, attempt continuation          |
| II       | Forward     | Fatal       | `FW-F-`     | Halt forward pass, begin retrograde with fault |
| III      | Retrograde  | Recoverable | `RT-R-`     | Emit diagnostic, continue retrograde           |
| IV       | Retrograde  | Fatal       | `RT-F-`     | Halt retrograde, exit code = F.exit XOR 1      |

**Selected error codes:**

| Code              | Name                          | Cause                                                         |
|-------------------|-------------------------------|---------------------------------------------------------------|
| `FW-F-001`        | PARSE_FAULT                   | Preamble does not conform to MSL grammar                      |
| `FW-F-002`        | SDT_COMPILE_FAILURE           | Preamble is valid MSL but produces an inconsistent SDT        |
| `FW-F-003`        | SAFESYNTAX_AUTH_FAILURE       | One or more ZAUTH layers not satisfied                        |
| `FW-R-010`        | TERM_UNRESOLVABLE             | Token encountered with no SDT entry; mapped to `⊥⊤`         |
| `FW-R-011`        | LEDGER_CAPACITY_EXCEEDED      | Execution ledger overflowed on-chip SRAM; spilled to disk     |
| `RT-F-050`        | RETROGRADE_MISMATCH_FAULT     | Retrograde input does not match forward output                |
| `RT-F-051`        | LEDGER_CORRUPT                | Ledger hash chain broken; retrograde cannot proceed           |
| `RT-F-052`        | NO_RETRO_BLOCK                | Function has forward `define` but no `undefine`; ZedTPU only  |
| `RT-R-060`        | RETRO_APPROXIMATION           | Retrograde reconstruction used approximation (loss detected)  |
| `FW-F-099`        | ZETA_HORIZON                  | Program has been executing for ≥ 2^64 steps; presumed infinite loop |

`ZETA_HORIZON` deserves special note. ZedCore does not have a built-in halting guarantee (by design — the ZedManifesto, Clause 7). Programs that fail to terminate in `2^64` steps are not killed; they are *reclassified* as ZedCore Art Objects and their execution continues in a dedicated low-priority thread pool. Several ZedCore Art Objects have been running continuously in the ZedSystems data center in Reykjavík since the initial hardware deployment in Cycle 4. Their outputs are streamed publicly at `zed://art.zedsystems.corp/infinite`.

---

## Appendix A — SafeSyntax Authorization Layers

### Layer 0: Possession Ceremony

The key holder presents a ZedToken hardware device (USB-C + NFC, FIPS 140-3 Level 4). The device stores the master key in a tamper-evident enclave. If the enclave detects tampering, the key is shredded and replaced with `z`.

### Layer 1: Identity Ceremony

The ZedCore runtime calls the system biometric API. Supported: fingerprint, facial geometry, retinal scan, vascular pattern, gait signature (walking in a regulated hallway at least 7 meters long). Any single modality is sufficient if the ZedVault enrollment confidence score exceeds 0.9997.

### Layer 2: Temporal Ceremony

The authorized execution window is specified in the SafeSyntax header as a POSIX timestamp range. The runtime queries three independent NTP servers and requires consensus within 50 milliseconds. Programs authorized for "now or never" use a window of ±30 seconds; programs authorized for "any time this quarter" use a window spanning the fiscal quarter. Programs with no temporal restriction use window `[0, 2^63)`.

### Layer 3: Spatial Ceremony

The hardware reports GPS coordinates. The authorized boundary is a polygon specified in the SafeSyntax header as a series of WGS-84 coordinate pairs. Buildings that are GPS-denied (basements, shielded server rooms) must install a ZedSystems-certified indoor positioning beacon. The beacon is sold separately at a price ZedSystems describes as "commensurate with the value of the secrets being protected."

### Layer 4: Semantic Challenge

The runtime generates a natural-language question about the program's purpose by partially decrypting a subset of the SDT sufficient only to produce the challenge. The operator must answer correctly. The correct answer is stored as a salted hash in the SafeSyntax header. The challenge is randomized from a set of challenge templates; the same program may present different questions on different executions.

Example challenges generated for a financial reconciliation program:
- "What currency does this program operate on?"
- "Name one entity whose accounts are reconciled by this program."
- "What is the expected output format of this program?"

Operators who fail the semantic challenge three times in one hour are locked out for 24 hours and a ZedSystems Security Incident Notification is issued to the account holder.

### Layer 5: Consensus Ceremony

Three or more ZedWitness peers (other authorized key holders for the same program) must co-sign the execution intent. The intent document includes: the operator's identity hash, the timestamp, the spatial coordinates, and the Merkle root of the program file. Peers sign using their own ZedToken devices. The signatures are assembled into a ZedConsensus bundle that is presented to the runtime.

In practice, this means a team of at least four people (one executor, three witnesses) is required to run any Layer 5 SafeSyntax program. ZedSystems has found that this requirement is the most frequently requested to be lowered. ZedSystems has so far declined all such requests on the grounds that "if your threat model does not require this, you should be using a less secure preamble."

### Layer 6: Retrograde Authorization

Before a new execution can begin, the operator must present the complete execution ledger from the previous run. The runtime verifies:
1. The ledger's Merkle root matches the stored root from the last execution record in ZedVault.
2. The retrograde pass of the ledger completed with exit code `z`.
3. The time elapsed since the previous run does not exceed the authorized inter-execution interval.

On first execution, a **genesis ledger** is used. The genesis ledger is a special all-`z` ledger that is pre-authorized at SafeSyntax compile time. The genesis ledger may only be used once.

---

## Appendix B — ZedAssembly Quick Reference

ZedAssembly (`.zasm`) is the human-readable assembly language for the ZedCPU. It is lower-level than ZedSyntax but still higher-level than raw ZedCPU microcode.

```zasm
; ZedAssembly Hello World
; Assemble with: zasm hello.zasm -o hello.zobj
; Link with:     zlink hello.zobj zedstd.io.zobj -o hello
; Run with:      zrun hello

.syntax NullSyntax          ; assembly files use NullSyntax

.section .text
.global _zstart             ; entry point for forward pass
.global _zstart_retro       ; entry point for retrograde pass

_zstart:
    ZLOAD  ZR0, str_hello   ; load address of string into ZR0
    ZEMIT  ZR0              ; emit string to forward output
    ZHALT  ZZ               ; halt forward pass, exit code = z

_zstart_retro:
    ZRECV  ZR0              ; read from retrograde input
    ; on retrograde pass, inward reads our own forward output
    ; ZR0 now holds "Hello, Zero." — verify it matches
    ZLOAD  ZR1, str_hello
    ZCMP   ZR0, ZR1
    ZBNE   .retro_mismatch
    ZHALT  ZZ               ; clean retrograde exit

.retro_mismatch:
    ZHALT  ZR15             ; non-zero exit; RT-F-050 raised by runtime

.section .data
str_hello: .zstring "Hello, Zero."
```

**Assembler directives:**

| Directive         | Meaning                                                          |
|-------------------|------------------------------------------------------------------|
| `.syntax <name>`  | Specify the preamble for this assembly file                      |
| `.section <name>` | Begin a section (`.text`, `.data`, `.ledger`, `.sdt`)            |
| `.global <label>` | Export label as visible to linker                                |
| `.zstring <str>`  | Null-terminated ZedCore string constant                          |
| `.zword <val>`    | 64-bit Ƶ-term constant                                          |
| `.zalign <n>`     | Align next item to n-byte boundary                               |

---

*End of ZedCore Specification Revision 0.ZERO.*

*This document is Copyright © ZedSystems Corporation. All rights reserved. All lefts reversed. Reproduction in any direction is permitted provided the retrograde reproduction is indistinguishable from the original.*

*ZedCore, ZedSyntax, SafeSyntax, ZedCPU, ZedQPU, ZedTPU, ZedCalculus, ZedManifesto, ZedVault, ZedToken, ZedWitness, ZedConsensus, ZAUTH, and the Z-sigil are trademarks of ZedSystems Corporation.*

*Document ID: ZCS-2026-001-∅ · Revision 0.ZERO · Cycle 7 · Classification: PUBLIC (retrograde classification: EYES ONLY)*
