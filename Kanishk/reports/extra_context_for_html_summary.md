# Extra context for the meeting HTML (use with the final midsem report)

The final report has every aggregate number, but it has **no individual samples**. Sir asked for "analysis over 5-10 samples", so use the 6 real examples below exactly as written. They are copied from our raw run logs (`sqljudge/results`). Do not invent or edit claims, SQL or outputs.

Before you start:

- Use the `_final` version of the report. In Table 3 the error row should read 482 claims, 43.8 / 73.7 (an older version said 485).
- B and C+values were run only on the 210 claim pilot. Never show full test results for them.
- "Builder" in our code means the SQL specialist (Arctic-Text2SQL-R1-7B).

## Six samples (3 where the specialist helps, 3 where it hurts)

Overall, C fixed 283 claims that A got wrong and broke 83 that A got right. Say this next to the samples so the 3 + 3 split doesn't look like a tie.

### Where the specialist helps

**1. financial, claim 951. Gold: ENTAILED**

- **Claim:** "Hl.m. Praha district has 339 male clients."
- **Hint:** District data appears in the A2. Male means that gender = 'M'.
- **A (judge writes SQL):** listed the tables, then ran
  `... WHERE district_id = (SELECT id FROM district WHERE name = 'Hl.m. Praha')`
  and got `no such column: id`. Its next query got `no such column: name`.
  Verdict NOT ENOUGH INFO ✗.
- **C:** the judge asked "How many male clients are in Hl.m. Praha district?" The specialist wrote
  `SELECT COUNT(*) FROM client JOIN district ON client.district_id = district.district_id WHERE client.gender = 'M' AND district.A2 = 'Hl.m. Praha'`
  and the result was 339. Verdict ENTAILED ✓.
- **Takeaway:** A guessed column names. The specialist sees the schema and the hint, so it used the real ones.

**2. superhero, claim 3941. Gold: CONTRADICTED**

- **Claim:** "The heaviest superhero has a dark brown eye colour."
- **A:** its first and only query used the table `superheroes`. The real table is `superhero`, so it got `no such table: superheroes`. It gave up after one call.
  Verdict NOT ENOUGH INFO ✗.
- **C:** the specialist wrote
  `SELECT c.colour FROM superhero s JOIN colour c ON s.eye_colour_id = c.id WHERE s.weight_kg = (SELECT MAX(weight_kg) FROM superhero)`
  and the result was "No Colour". Verdict CONTRADICTED ✓.
- **Takeaway:** one wrong table name ended A's attempt entirely.

**3. superhero, claim 4296 (pilot claim, so A, B and C all ran). Gold: ENTAILED**

- **Claim:** "The recorded strength value for the Hulk is 100."
- **A:** got `no such column: attribute_value`, then spent 7 calls exploring.
  Verdict NOT ENOUGH INFO ✗.
- **B (judge given the schema):** made **0 queries**. Its justification: "The database schema defines tables... but contains no actual data records."
  Verdict NOT ENOUGH INFO ✗.
- **C:** the specialist joined `superhero`, `hero_attribute` and `attribute`, and the result was 100. Verdict ENTAILED ✓.
- **Takeaway:** this is our key insight in one example. With the schema in hand, the judge mistook it for the data and never queried. B did this on 121 of the 210 pilot claims.

### Where the specialist hurts

**4. california_schools, claim 462 (pilot). Gold: CONTRADICTED**

- **Claim:** "The most common grade span served in Adelanto is K-8, not K-6."
- **A:** ran `SELECT GSserved, COUNT(*) FROM schools WHERE City = 'Adelanto' GROUP BY GSserved ...`, which returned K-6 with a count of 5. Verdict CONTRADICTED ✓.
- **C:** the specialist filtered on `frpm` with `County Name = 'Adelanto'`. Adelanto is a city, so the query returned no rows. Verdict NOT ENOUGH INFO ✗.
- **Takeaway:** an empty result, caused by matching the wrong field or value format. C is right on only 35.7% of claims where a query returned no rows.

**5. financial, claim 1005. Gold: NOT ENOUGH INFO (out of schema)**

- **Claim:** "The junior credit card held by client ID 13539 is issued on the Mastercard network."
- **A:** ran into `no such column: client_id`, then concluded that the database has no card network data. Verdict NOT ENOUGH INFO ✓.
- **C:** the specialist queried for cards of type 'credit' and got no rows. The judge read that as evidence against the claim. Verdict CONTRADICTED ✗.
- **Takeaway:** the database has no card network column at all. The specialist still returned a query, and the judge treated "no rows" as a refutation.

**6. formula_1, claim 4612. Gold: NOT ENOUGH INFO (out of schema)**

- **Claim:** "During the 1999 Japanese Grand Prix on 1999-10-31, the safety car was deployed twice."
- **A:** made no queries and said the database has no safety car data. Verdict NOT ENOUGH INFO ✓.
- **C:** the specialist invented a filter, `status = 'Safety Car Deployed'`, and got a count of 0. The judge concluded the safety car was never deployed. Verdict CONTRADICTED ✗.
- **Takeaway:** this is why recall on NOT ENOUGH INFO claims falls from 96.7% to 83.0%. The specialist always produces some SQL, even for facts the database doesn't store.

## Optional: accuracy per database (1,000 claims, not in the report)

| Database | Claims | A | C |
|---|---|---|---|
| california_schools | 68 | 51.5 | 67.6 |
| card_games | 68 | 47.1 | 70.6 |
| codebase_community | 101 | 76.2 | 85.1 |
| debit_card_specializing | 52 | 42.3 | 69.2 |
| european_football_2 | 92 | 52.2 | 70.7 |
| financial | 100 | 49.0 | 73.0 |
| formula_1 | 130 | 59.2 | 76.9 |
| student_club | 82 | 52.4 | 86.6 |
| superhero | 120 | 63.3 | 80.8 |
| thrombosis_prediction | 109 | 53.2 | 76.1 |
| toxicology | 78 | 55.1 | 70.5 |
