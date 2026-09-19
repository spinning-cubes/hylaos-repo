import secrets
import string

# Generate an 8-character code formatted as XXXX-XXXX
alphabet = string.ascii_uppercase + string.digits
code = "".join(secrets.choice(alphabet) for _ in range(8))
formatted_code = f"{code[:4]}-{code[4:]}"

with open("LICENSEE-CODES", "a", encoding="utf-8") as f:
    f.write(f"{formatted_code}\n")

print(f"Appended code: {formatted_code}")