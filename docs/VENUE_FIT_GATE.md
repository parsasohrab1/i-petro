# Venue-fit gate (before any submission)

Created after the desk rejection of "Certified Facies Sets from Well Logs ..." by Energy Geoscience
(special issue "Advances in AI for Energy Systems and Subsurface Engineering"). The editor's reason was
"content and appeal not of the sufficient level"; no further detail was given, so the causes below are
inferences from the manuscript and the call text, not statements by the editor.

## Likely causes
1. **Scope/appeal mismatch.** The call stresses physics-informed, surrogate, integrated or autonomous AI,
   reservoir characterisation, geothermal/CO2, digital twins, agentic AI, federated learning, and wants real
   case studies or forward-looking perspectives. The manuscript is a benchmark of standard components
   (forest/boosting, split conformal, Viterbi) on two public data sets; it states that all methods are standard.
2. **Low significance of the headline.** Base accuracy 0.53 on SEG 2016, decoding gives no reliable gain,
   referral impractical on SEG 2016. The main finding (marginal coverage does not hold per well; local
   recalibration helps) is useful but incremental and close to known group-conditional/local calibration ideas.
3. **No geoscience payoff.** No geological interpretation, no decision-cost analysis (e.g. reservoir vs seal
   confusion), no field case with an operator.
4. **Packaging.** Method-jargon title; code only "on request" in a private repository; single author with a company affiliation.
5. **Process.** The venue was chosen from a deadline and topic keyword; there was no fit check, no comparison with recent
   papers of the journal, and no pre-submission enquiry.

## Gate (all items must be answered in the dashboard before status "ready to submit")
| # | Check | Pass rule |
|---|-------|-----------|
| 1 | Scope sentence | Quote the venue's scope/CFP line the paper answers, and the CFP topic it maps to |
| 2 | Paper type | Venue accepts this type (benchmark, negative result, method, case study); if not, choose another venue or change the paper |
| 3 | Novelty statement | One sentence: what is new versus the 3 closest published papers (cite them) |
| 4 | Recent-paper comparison | Read 3 recent papers from the same journal/issue; ours is comparable in depth, data and domain insight |
| 5 | Domain payoff | A result a practitioner of that field can act on, stated in the abstract |
| 6 | Data | At least one real, non-trivial case beyond a public benchmark, or the venue explicitly accepts benchmark studies |
| 7 | Reproducibility | Code/data availability meets the venue policy (public repo or archived DOI, after owner/patent approval) |
| 8 | Title/abstract | Title states the finding, not a list of techniques; first sentence names the domain problem |
| 9 | Enquiry | For selective journals and special issues, send a short pre-submission enquiry (title, abstract, one-line fit) to the editor and record the reply |
| 10 | Patent / owner | Patent attorney and owner approval recorded (existing rule) |

Score: any "fail" on 1-5 blocks submission. Items 6-9 are fixed or explicitly waived by the owner in writing.

## Retrospective use
Run the gate on every entry in `settings/article_calls` whose status is not yet submitted.
