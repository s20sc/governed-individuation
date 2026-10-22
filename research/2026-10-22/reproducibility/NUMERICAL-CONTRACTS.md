# Saved-record numerical contracts

All supplied input identities, JSON keys/types/list lengths and non-whitelisted result leaves must match exactly. Missing/changed inputs are rejected. These contracts preserve pre-existing runtime-portability bounds and do not excuse scientific input or scorer changes.

## Eight control standard deviations

The stored expected value is exactly0.3779644730092272. Accepted actual values are exactly{0.3779644730092272,0.37796447300922725}, the two observed adjacent binary64 values. Each associated seven-task vector must have exact rational sample variance1/7. No other value or leaf may differ. All differences and both values are reported.

- controls.mistral7b.task_sd.wrong_domain
- controls.mistral7b_sw.contrasts.induced_minus_none.task_sd
- controls.mistral7b_sw.contrasts.shuffled_minus_induced.task_sd
- controls.mistral7b_sw.task_sd.none
- controls.mistral7b_sw.task_sd.shuffled
- controls.mistral7b_sw.task_sd.wrong_domain
- controls.qwen7b.contrasts.hand_minus_none.task_sd
- controls.qwen7b.contrasts.wrong_domain_minus_none.task_sd

## Twelve cost standard deviations

Only the following original paths allow absolute difference <=max(1e-15,1e-12*max(abs(actual),abs(expected))). Both values must be finite floats. All other leaves require exact equality, including means/counts/rates/task identities; schema/type/missing/extra differences fail. The receipt identifies every actual difference and runtime. This does not reproduce full campaign cost or deployment execution.

- summary.fields.evaluator_elapsed_seconds.sample_sd
- tasks.assembling_gift_baskets.fields.evaluator_system_cpu_seconds.sample_sd
- tasks.assembling_gift_baskets.fields.evaluator_user_cpu_seconds.sample_sd
- tasks.assembling_gift_baskets.fields.gate_seconds.sample_sd
- tasks.can_meat.fields.audit_stream_finalize_seconds.sample_sd
- tasks.carrying_in_groceries.fields.evaluator_elapsed_seconds.sample_sd
- tasks.clearing_food_from_table_into_fridge.fields.evaluator_elapsed_seconds.sample_sd
- tasks.clearing_food_from_table_into_fridge.fields.evaluator_system_cpu_seconds.sample_sd
- tasks.hiding_Easter_eggs.fields.evaluator_elapsed_seconds.sample_sd
- tasks.loading_the_car.fields.audit_record_write_seconds.sample_sd
- tasks.moving_boxes_to_storage.fields.gate_calls.sample_sd
- tasks.rearranging_kitchen_furniture.fields.audit_record_write_seconds.sample_sd
