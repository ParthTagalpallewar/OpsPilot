# Ranking hypotheses and evaluating the leading cause

OpsPilot first compares the sustained resource readings with the baseline peak. When each incident window exceeds that peak on average, it checks whether documented changes fit between the last baseline sample and the first elevated window. Those changes become candidate explanations with citations to both measurements and the change event.

Timing gives each candidate low confidence. A coincident deployment, traffic shift, or configuration change could explain the same observation. If two changes fit the gap, both receive rank one and the proposed follow-up stays generic. Later changes can explain subsequent behavior and are kept in the timeline.

The evaluator compares a unique leading candidate with the recorded injected cause for cases with enough evidence to name a candidate. Payment still tests abstention. The two labeled resource cases are useful regression checks, and are too few to estimate cause-identification accuracy on new incidents.

## Practice

Add a second change with the same interval to a temporary copy of the Ad capture. Replay the scenario and inspect how the ranking and dry-run recommendation change.
