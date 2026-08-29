/**
 * Exact rational arithmetic — TS port of Python `fractions.Fraction` +
 * `math.gcd`/`math.lcm` (design_001 §4, B2). No floats in the algebra path:
 * matrix entries are weights/tokens of v1 test nets, far below 2^53 so JS
 * integer arithmetic is exact. Normalization mirrors `fractions.Fraction`:
 * denominator always > 0, reduced by gcd(|num|, den).
 *
 * Semantics pinned by design_001 §4 + §10.1 (fraction behaviors).
 */

/** math.gcd semantics: gcd(0,0)=0; signs → abs; gcd(0,x)=abs(x). */
export function gcd(a: number, b: number): number {
  a = Math.abs(a);
  b = Math.abs(b);
  while (b !== 0) {
    const t = b;
    b = a % b;
    a = t;
  }
  return a;
}

/** a/gcd(a,b)*b (overflow-safe order); lcm(0,x)=0 (Python math.lcm). */
export function lcm(a: number, b: number): number {
  if (a === 0 || b === 0) return 0;
  return Math.abs(a) / gcd(a, b) * Math.abs(b);
}

export class Fraction {
  /** Signed numerator. */
  readonly num: number;
  /** Denominator — always > 0 (normalized). */
  readonly den: number;

  constructor(num: number, den: number = 1) {
    // B2 invariant: no floats in the algebra path.
    if (!Number.isInteger(num) || !Number.isInteger(den)) {
      throw new RangeError("Fraction requires integer numerator and denominator");
    }
    if (den === 0) {
      throw new RangeError("Fraction denominator cannot be zero");
    }
    if (den < 0) {
      num = -num;
      den = -den;
    }
    const d = gcd(Math.abs(num), den);
    // Python int canonicalization: -0 normalizes to 0 (JS -x of 0 is -0).
    this.num = num / d === 0 ? 0 : num / d;
    this.den = den / d;
  }

  static zero(): Fraction {
    return new Fraction(0, 1);
  }

  add(o: Fraction): Fraction {
    return new Fraction(this.num * o.den + o.num * this.den, this.den * o.den);
  }

  sub(o: Fraction): Fraction {
    return new Fraction(this.num * o.den - o.num * this.den, this.den * o.den);
  }

  mul(o: Fraction): Fraction {
    return new Fraction(this.num * o.num, this.den * o.den);
  }

  div(o: Fraction): Fraction {
    if (o.isZero()) {
      throw new RangeError("Fraction division by zero");
    }
    return new Fraction(this.num * o.den, this.den * o.num);
  }

  neg(): Fraction {
    return new Fraction(-this.num, this.den);
  }

  isZero(): boolean {
    return this.num === 0;
  }

  equals(o: Fraction): boolean {
    return this.num === o.num && this.den === o.den;
  }

  /** Exact int? (den===1). Used by tests/vector checks. */
  toInt(): number {
    if (this.den !== 1) {
      throw new RangeError("Fraction is not an exact integer");
    }
    return this.num;
  }
}