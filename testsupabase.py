from supabase import create_client, Client

url = "https://nlpofscrwwvubtugcrqa.supabase.co"  # Remplace par l'URL de ton projet Supabase
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5scG9mc2Nyd3d2dWJ0dWdjcnFhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjQ3ODQ1NTUsImV4cCI6MjA0MDM2MDU1NX0.YUyPvm96JrZ7NJpYyLhgXmrN8gEQ_SVcpUlHVPHToBg"
supabase: Client = create_client(url, key)

data = supabase.table("checklists").select("*").execute()
print(data)
