from pwdlib import PasswordHash

pwd = PasswordHash.recommended()

print(pwd.hash("54321"))