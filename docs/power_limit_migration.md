# Power limit and OPP migration

The historical `power_limit_*` methods configured OPP, not the operating power limit. They are deprecated but retain that behavior with warnings to prevent a silent protection-setting change. Use `output_power_limit_set/query` for the actual power limit and `opp_threshold_set/query` plus `opp_enable/query` for OPP. The guide index places power limit on pp.76–77 and OPP on pp.78–80. Model-specific maximum ranges and physical qualification remain separate. Do not treat a power limit as a safety trip threshold.
