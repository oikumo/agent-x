/**
 * Typed error hierarchy — TS port of `src/agentx/model/petri_net/errors.py`.
 * `ValueError` deliberately does NOT extend PetriNetError (Python parity, A7).
 */

export class PetriNetError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PetriNetError";
  }
}

/** The net structure is invalid (incl. duplicate arcs/places, ambiguity). */
export class InvalidModelError extends PetriNetError {
  constructor(message: string) {
    super(message);
    this.name = "InvalidModelError";
  }
}

/** addPlace() with an existing place name. */
export class DuplicatePlaceError extends InvalidModelError {
  constructor(message: string) {
    super(message);
    this.name = "DuplicatePlaceError";
  }
}

/** addInput()/addOutput() for an arc endpoint pair that already exists. */
export class DuplicateArcError extends InvalidModelError {
  constructor(message: string) {
    super(message);
    this.name = "DuplicateArcError";
  }
}

/** A referenced place does not exist in the net. */
export class UnknownPlaceError extends PetriNetError {
  constructor(message: string) {
    super(message);
    this.name = "UnknownPlaceError";
  }
}

/** A referenced transition does not exist in the net. */
export class UnknownTransitionError extends PetriNetError {
  constructor(message: string) {
    super(message);
    this.name = "UnknownTransitionError";
  }
}

/** fireMarking()/fire() on a transition disabled in the given marking. */
export class TransitionNotEnabledError extends PetriNetError {
  constructor(message: string) {
    super(message);
    this.name = "TransitionNotEnabledError";
  }
}

/** Plain value-validation failure — NOT a PetriNetError (mirrors Python ValueError). */
export class ValueError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ValueError";
  }
}
