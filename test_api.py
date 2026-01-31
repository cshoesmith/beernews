from api.index import app

with app.test_client() as client:
    # Test stats
    resp = client.get('/api/stats')
    stats = resp.json
    print('Stats:', stats)
    print()
    
    # Test new releases
    resp = client.get('/api/beers/new')
    beers = resp.json
    print(f'New releases: {len(beers)}')
    for b in beers[-3:]:  # Last 3
        print(f'  - {b["name"]} ({b["style"]}) - Released: {b["release_date"][:10]}')
    
    print()
    
    # Test recommendations
    resp = client.get('/api/recommendations?suburb=Newtown')
    recs = resp.json
    print(f'Newtown recommendations: {len(recs)}')
    for r in recs[:2]:
        print(f'  - {r["venue"]["name"]}: {len(r["new_beers"])} new beers')
