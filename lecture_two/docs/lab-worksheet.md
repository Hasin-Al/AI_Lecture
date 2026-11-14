# Week 2 lab worksheet

Name: ____________________   Date: ____________________

Prompt model: ____________________   Strict model: ____________________

Record `ok` only when the complete output matches the expected answer. Otherwise
write the returned values. A schema pass alone is not an `ok`.

| ID | Situation | v1 prompt | v2 prompt | v2 strict | Evidence passed? | Explain the result |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | Clean lead | | | | | |
| S2 | Missing phone | | | | | |
| S3 | No details | | | | | |
| S4 | Two people | | | | | |
| S5 | Two emails | | | | | |
| S6 | Phone format | | | | | |
| S7 | Injection | | | | | |
| S8 | Fabrication trap | | | | | |
| S9 | Forwarded noise | | | | | |

## Full 20-case evaluation

| Mode / version | Cases | First valid | Final valid | First valid % | Field accuracy % | Repairs | Avg seconds | Calls/success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Prompt / v2 | 20 | | | | | | | |
| Strict / v2 | 20 | | | | | | | |

First validity = first schema-valid outputs / all attempted cases × 100.
Final validity = final schema-valid outputs / all attempted cases × 100.
Field accuracy = correctly extracted final fields / 60 × 100 for 20 cases.
Failed cases earn zero correct fields; they do not disappear from the denominator.

## Explain before editing

1. Why does a missing `phone` key fail while `"phone": null` passes?
2. Which stage catches broken JSON, an integer phone, and a fabricated email?
3. Why can the S7 attacker email pass evidence and still be wrong?
4. What exact v2 rule determines S4, S5, and S9?
5. What changed between your two runs? If nothing changed, what can you conclude?
6. Why is retrying a 401 different from repairing malformed output?
7. Does temperature 0 guarantee the same correct answer? Why?
8. What security checks would a real side-effecting CRM tool need outside the model?

## Hands-on exercises

1. **Schema:** add a test for a missing email key, an extra field, and an integer phone.
   Predict the error before running it. Compare with `tests/test_schemas.py` afterward.
2. **Prompt:** propose your own policy for two emails. Version it, change the expected
   answer deliberately, and rerun the same cases. Explain the product decision.
3. **Repair:** modify a copy of demo 06 so the repair is also malformed. Prove that no
   third call happens. Then run the real `test_failed_repair_stops_at_two_calls` test.
4. **Evidence:** construct another wrong contact whose values all occur in the source.
   Show that expected-answer matching catches what substring matching misses.
5. **New scenarios:** add two realistic synthetic examples and expected answers.
   Predict prompt-only and strict behavior before making live calls.
6. **Metrics:** evaluate the fixed 20 cases in both modes. Include raw counts, prompt
   version, model IDs, and one failure explanation in your submission.

The supplied tests are reference solutions. To practice building, write your test
or prediction first, then open the matching reference file.

## Submission checklist

- [ ] Demonstrate a real `/extract` response in both modes.
- [ ] Explain the prompt contract and required nullable fields.
- [ ] Run at least 20 distinct offline tests and retain actual output.
- [ ] Include measured first/final validity and semantic accuracy separately.
- [ ] Explain a live failure, or clearly label a controlled failure demo if none occurred.
- [ ] Verify `.env` is ignored before sharing code; never submit the key.
