## random_values

mint_identity: [BEHAVIOR] MUST return the canonical text of a new random UUID on every call, its randomness taken only from the operating system's random source, never from a seeded pseudo-random generator, the clock, a counter or any input; whether the identity is free is left to the writing module, which checks it.
make_secret_value: [BEHAVIOR] MUST draw exactly as many bytes as the imported SECRET_MIN_BYTES constant names from the operating system's random source and MUST return them in a text form a cookie value and an HTML form field carry without escaping, a fresh value on every call.
make_secret_value: [SECURITY_BOUNDARY] MUST take its bytes only from the operating system's random source, never from a seeded pseudo-random generator, and MUST NOT keep, log or put into a diagnostic the value it makes.
equal_in_constant_time: [SECURITY_BOUNDARY] MUST answer whether presented and held are equal using a comparison whose time does not depend on the position of the first differing byte, and MUST answer false, without raising, when their lengths differ.
equal_in_constant_time: [FORBIDDEN_ACTION] MUST NOT keep, log or put into a diagnostic either value it compares.
