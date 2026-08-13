# State 7 trace repair — Flow 4 rule addresses

calculate_plan_actual: [RULE_REFERENCE] Build the baseline at the accepted item grain from = rules.plan_actual.analysis_grain; planned quantity and amount use = rules.plan_actual.planned_quantity_source and = rules.plan_actual.planned_amount_source; actual quantity and amount use = rules.plan_actual.actual_quantity_source and = rules.plan_actual.actual_amount_source.

calculate_plan_actual: [RULE_REFERENCE] Aggregate confirmed matched lines according to = rules.plan_actual.matched_line_aggregation; quantity variance uses = rules.plan_actual.quantity_variance; amount variance uses = rules.plan_actual.amount_variance; remaining quantity uses = rules.plan_actual.remaining_quantity.

calculate_plan_actual: [RULE_REFERENCE] Keep unmatched actual spend in the project bucket according to = rules.plan_actual.unmatched_actual_contributes_to_project_actual and out of item actual according to = rules.plan_actual.unmatched_actual_contributes_to_item_actual.

calculate_plan_actual: [RULE_REFERENCE] Unit comparison must obey = rules.plan_actual.implicit_unit_conversion_allowed; currency comparison must obey = rules.plan_actual.implicit_currency_conversion_allowed; monetary and tax-basis comparison must obey = rules.plan_actual.implicit_tax_basis_conversion_allowed.
