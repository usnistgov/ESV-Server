# Validation Script Framework: `VsfConfig/`

The `VsfConfig` directory implements a JSON-driven validation framework used to enforce business rules on request payloads. It decouples validation logic from the codebase, allowing rules to be defined and modified as data structures without requiring recompilation of the core application.

## Framework Architecture

The framework consists of three primary components: **Validation Trees**, **Rule Scripts**, and **Rule Templates**.

### 1. Validation Trees (`/ValidationTrees`)
Validation trees define *where* and *when* rules are applied to a data model. They map the structure of a payload to specific rule scripts.

- **Structure**: Each tree (e.g., `CertifyRequest/combined.json`) is a hierarchical mapping of the payload.
- **Node Types**:
  - `rootNode`: The entry point for the model validation.
  - `leaf`: Maps a specific property (identified by `internalIdentifier`) to one or more rule scripts.
  - `parent`: Represents a nested object containing its own set of `nodes`.
  - `list`: Represents a collection. It can define rules for the list itself (e.g., `listMinCount.json`) and rules for individual `listItem` elements.
- **Execution Flow**:
  - `vsfScriptFiles`: An array of scripts executed for that node.
  - `runBeforeListItem` / `runAfterListItem`: Hooks to execute rules before or after iterating through list items.
  - `breakOnError`: Boolean flag to determine if validation should stop immediately upon a rule failure.

### 2. Rule Scripts (`/RuleScripts`)
Rule scripts contain the actual logic for validation. They are categorized into:
- **CommonRules/**: Reusable, generic validators (e.g., `notNull.json`, `listIsUnique.json`, `validObjectId.json`).
- **Rules/**: Domain-specific validators tailored to particular request types (e.g., `CertifyRequest`, `RegisterRequest`).

### 3. Rule Templates (`/RuleScriptTemplates`)
Templates define the schema for creating new rule scripts, ensuring consistency.

- **`template-rule.json`**: The basic building block.
  - `lineType: "Rule"`: Executes a specific check.
  - `ruleType: "External"`: Indicates the rule logic is handled by an external assembly/provider.
  - `parameters.ruleText`: The specific logic or identifier for the rule.
- **`template-branch.json`**: Implements conditional logic.
  - Supports `if`, `elseif`, and `else` blocks.
  - Each block contains `scriptLines`, allowing for complex, nested validation flows based on the state of the payload.

## Rule Examples & Line Types

The framework uses several `lineType` options to compose complex validation logic:

### Common Line Types
- **`Rule`**: The primary validation check.
  - *Example*: `currentProperty != null` in `notNull.json` ensures a field is present.
- **`ImportScript`**: Composes rules by including another JSON script.
  - *Example*: `moduleId.json` imports `notNull.json` before performing its own checks.
- **`State`**: Stores a value in a local context for later use within the same script.
  - *Example*: Creating a `claimVerifierObj` using `ReferenceIdClaimVerifier(...)` to validate an ID claim.
- **`Assert`**: A boolean check that must be true for the validation to continue.
  - *Example*: Checking if `jwtService != null` before attempting to use it.
- **`Information`**: Logs diagnostic information.
  - *Example*: Printing the resolved module name via `String.Format`.

### Complex Rule Examples
- **`listMinCount.json`**: Combines an `ImportScript` (for null check) and a `Rule` (`currentProperty.Count() > 0`) to ensure a list is both present and non-empty.
- **`rbgIdClaim.json`**: Demonstrates a full workflow:
  1. Imports basic null checks.
  2. Asserts required services (`jwtService`) are available.
  3. Uses `State` to instantiate a verifier and fetch JWT claims.
  4. Executes an `External` rule to verify the claims against the property value.

## Summary of Workflow


1. **Payload Identification**: When a request is received, the system identifies the corresponding **Validation Tree** based on the payload type.
2. **Tree Traversal**: The validation engine traverses the tree, matching the payload's properties to the `internalIdentifier` defined in the tree nodes.
3. **Script Execution**: For every match, the engine executes the associated **Rule Scripts**.
4. **Conditional Logic**: If a script uses a `Branch` line type, the engine evaluates the `if/elseif` conditions to determine which subsequent `scriptLines` to execute.
5. **External Validation**: Rules marked as `External` are dispatched to the appropriate backend validator implementation to perform the actual check.