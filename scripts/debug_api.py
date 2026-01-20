"""Debug: Finde Kampagne mit echten Daten"""
import asyncio
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv('HIRINGS_API_TOKEN')
    base = 'https://high-office.hirings.cloud/api/v1'
    
    async with httpx.AsyncClient() as client:
        # Hole alle Companies
        resp = await client.get(f'{base}/companies/names', headers={'Authorization': token})
        companies = resp.json().get('companies', [])
        
        print(f"Suche Kampagne mit Daten in {len(companies)} Firmen...\n")
        
        # Suche Kampagne mit echten Daten (nicht nur Test)
        for company in companies[:20]:  # Erste 20
            cid = company['id']
            name = company['name']
            
            resp = await client.get(f'{base}/companies/{cid}/campaigns', headers={'Authorization': token})
            campaigns = resp.json().get('campaigns', [])
            
            for camp in campaigns[:3]:
                camp_id = camp['id']
                
                # Hole Transcript
                resp = await client.get(
                    f'{base}/onboarding/{cid}/transcript/{camp_id}',
                    headers={'Authorization': token}
                )
                data = resp.json()
                
                # Pruefe ob echte Daten vorhanden
                transcript = data.get('transcript', {})
                pages = transcript.get('pages', [])
                
                has_data = False
                for page in pages:
                    prompts = page.get('prompts', [])
                    if len(prompts) > 2:  # Mehr als 2 Prompts = echte Daten
                        has_data = True
                        break
                
                if has_data:
                    print(f"GEFUNDEN: {name} (ID: {cid})")
                    print(f"Kampagne: {camp.get('title', 'N/A')} (ID: {camp_id})")
                    print("-" * 60)
                    print(json.dumps(data, indent=2, ensure_ascii=False)[:5000])
                    return

        print("Keine Kampagne mit echten Daten gefunden in ersten 20 Firmen")

asyncio.run(main())
