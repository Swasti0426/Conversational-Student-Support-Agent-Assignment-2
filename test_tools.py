
from tools import get_fee_status, check_scholarship_status


print("\n--- TEST 1: Fee Status ---")
result = get_fee_status("STU1001")
print(result)

print("\n--- TEST 2: Scholarship Status ---")
result = check_scholarship_status("STU1002")
print(result)

print("\n--- TEST 3: Unknown Student ---")
result = get_fee_status("STU9999")
print(result)
