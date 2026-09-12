# Build

Implements and proves already-defined Project behavior.

## Purpose

Change implementation, tests, generated assets, and other executable/project artifacts so the current Goal becomes true without silently redefining Project intent.

## Owns

Build has no single durable product-authority artifact. Its skills own bounded implementation, test, proof, and repair state.

The current Goal constrains what work is in bounds. The active Project model supplies implementation authority:

- `spec`: relevant stable Spec scopes plus the Goal boundary
- `repository-native`: current transient Goal Spec plus named native constraints and the Goal boundary

## Skills

- `implement`
- `proof`
- `repair`
- `check`

## Dependencies

Consumes the Goal and current Project authority. When implementation exposes a missing consequential Domain/App/Style/Tech decision, stop that dependent work and route the decision through Project Define/owning reasoning before continuing.

## Invariants

- implementation does not silently specify
- Build does not override active Project authority
- conflicts between Goal, Goal Spec/Spec scopes, and native authority are resolved through their owners before coding continues
- tests prove intended behavior rather than retroactively defining it by accident
- implementation remains bounded by the current Goal
