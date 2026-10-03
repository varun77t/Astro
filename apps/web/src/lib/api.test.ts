import { describe, expect, it } from "vitest";
import { toApiError } from "./api";

describe("toApiError", () => {
  it("reads our coded errors, including ambiguous-time options", () => {
    const err = toApiError(422, {
      detail: {
        code: "ambiguous_local_time",
        message: "01:30 occurred twice",
        options_utc: ["2021-11-07T05:30:00+00:00", "2021-11-07T06:30:00+00:00"],
      },
    });
    expect(err.code).toBe("ambiguous_local_time");
    expect(err.message).toBe("01:30 occurred twice");
    expect(err.optionsUtc).toHaveLength(2);
  });

  it("flattens Pydantic validation errors", () => {
    const err = toApiError(422, {
      detail: [{ loc: ["body"], msg: "Value error, Birth year must be between 1800 and 2100." }],
    });
    expect(err.code).toBe("validation_error");
    expect(err.message).toBe("Birth year must be between 1800 and 2100.");
  });

  it("falls back for unexpected bodies", () => {
    expect(toApiError(500, null).code).toBe("unknown");
  });
});
