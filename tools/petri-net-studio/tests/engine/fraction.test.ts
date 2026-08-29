// @vitest-environment node
/**
 * Fraction tests — design_001 §10.1 (fraction behaviors).
 * Mirrors Python `fractions.Fraction` + `math.gcd`/`math.lcm` semantics
 * (B2): gcd(0,0)=0 · gcd(0,x)=|x| · gcd negatives → abs · lcm ·
 * Fraction normalize · add/sub/mul/div exact · neg · isZero · toInt.
 */

import { describe, expect, it } from "vitest";

import { Fraction, gcd, lcm } from "../../src/engine/fraction.js";

describe("gcd", () => {
  it("gcd(0,0)=0", () => {
    expect(gcd(0, 0)).toBe(0);
  });

  it("gcd(0,x)=|x|", () => {
    expect(gcd(0, 5)).toBe(5);
    expect(gcd(5, 0)).toBe(5);
    expect(gcd(0, -7)).toBe(7);
    expect(gcd(-7, 0)).toBe(7);
  });

  it("gcd negatives -> abs", () => {
    expect(gcd(-12, 18)).toBe(6);
    expect(gcd(12, -18)).toBe(6);
    expect(gcd(-12, -18)).toBe(6);
    expect(gcd(21, 14)).toBe(7);
  });
});

describe("lcm", () => {
  it("lcm basics", () => {
    expect(lcm(4, 6)).toBe(12);
    expect(lcm(5, 7)).toBe(35);
    expect(lcm(21, 6)).toBe(42);
  });

  it("lcm(0,x)=0", () => {
    expect(lcm(0, 5)).toBe(0);
    expect(lcm(5, 0)).toBe(0);
  });
});

describe("Fraction normalization", () => {
  it("1/2", () => {
    const f = new Fraction(1, 2);
    expect(f.num).toBe(1);
    expect(f.den).toBe(2);
  });

  it("-1/2", () => {
    const f = new Fraction(-1, 2);
    expect(f.num).toBe(-1);
    expect(f.den).toBe(2);
  });

  it("2/4 -> 1/2", () => {
    const f = new Fraction(2, 4);
    expect(f.num).toBe(1);
    expect(f.den).toBe(2);
  });

  it("1/-2 -> -1/2", () => {
    const f = new Fraction(1, -2);
    expect(f.num).toBe(-1);
    expect(f.den).toBe(2);
  });

  it("0/5 -> 0/1", () => {
    const f = new Fraction(0, 5);
    expect(f.num).toBe(0);
    expect(f.den).toBe(1);
  });

  it("den defaults to 1", () => {
    const f = new Fraction(3);
    expect(f.num).toBe(3);
    expect(f.den).toBe(1);
  });

  it("den=0 throws RangeError", () => {
    expect(() => new Fraction(1, 0)).toThrow(RangeError);
    expect(() => new Fraction(1, 0)).toThrow("denominator");
  });
});

describe("Fraction arithmetic (exact)", () => {
  it("add", () => {
    expect(new Fraction(1, 2).add(new Fraction(1, 3)).equals(new Fraction(5, 6))).toBe(true);
  });

  it("sub", () => {
    expect(new Fraction(3, 4).sub(new Fraction(1, 2)).equals(new Fraction(1, 4))).toBe(true);
  });

  it("mul", () => {
    expect(new Fraction(2, 3).mul(new Fraction(3, 4)).equals(new Fraction(1, 2))).toBe(true);
  });

  it("div", () => {
    expect(new Fraction(1, 2).div(new Fraction(2, 3)).equals(new Fraction(3, 4))).toBe(true);
    expect(new Fraction(1, 3).div(new Fraction(2)).equals(new Fraction(1, 6))).toBe(true);
  });

  it("div by zero throws RangeError", () => {
    expect(() => new Fraction(1, 2).div(Fraction.zero())).toThrow(RangeError);
  });

  it("arithmetic keeps exact normalized form", () => {
    const f = new Fraction(1, 6).add(new Fraction(1, 6));
    expect(f.num).toBe(1);
    expect(f.den).toBe(3);
  });
});

describe("Fraction misc", () => {
  it("neg", () => {
    const f = new Fraction(1, 2).neg();
    expect(f.num).toBe(-1);
    expect(f.den).toBe(2);
    expect(new Fraction(-1, 2).neg().equals(new Fraction(1, 2))).toBe(true);
  });

  it("isZero", () => {
    expect(new Fraction(0, 5).isZero()).toBe(true);
    expect(new Fraction(1, 2).isZero()).toBe(false);
  });

  it("equals", () => {
    expect(new Fraction(1, 2).equals(new Fraction(2, 4))).toBe(true);
    expect(new Fraction(1, 2).equals(new Fraction(1, 3))).toBe(false);
    expect(new Fraction(-1, 2).equals(new Fraction(1, -2))).toBe(true);
  });

  it("toInt exact-only", () => {
    expect(new Fraction(4, 2).toInt()).toBe(2);
    expect(new Fraction(3, 1).toInt()).toBe(3);
    expect(new Fraction(0, 5).toInt()).toBe(0);
    expect(() => new Fraction(1, 2).toInt()).toThrow(RangeError);
  });
});