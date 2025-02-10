from streamlit_authenticator import Hasher

hashed_passwords = Hasher(["adminpass", "userpass"]).generate()
print(hashed_passwords)
