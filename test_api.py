from main import app

with app.test_client() as client:
    # Test stats
    resp = client.get('/api/stats')
    print('Stats:', resp.json)
    
    # Test recommendations with user location (Newtown area)
    resp = client.get('/api/recommendations?user_lat=-33.8969&user_lng=151.1795')
    recs = resp.json
    print('\nRecommendations sorted by distance:')
    for r in recs[:3]:
        dist = r.get('distance_km')
        dist_str = f"{dist:.2f} km" if dist is not None else "N/A"
        print(f"  - {r['venue']['name']}: {dist_str} - {r['reason']}")
    
    # Test filter by suburb
    resp = client.get('/api/recommendations?suburb=Newtown')
    print(f"\nNewtown venues: {len(resp.json)}")
    
    # Test filter by style
    resp = client.get('/api/recommendations?liked_styles=Sour,IPA')
    print(f"Sour/IPA recommendations: {len(resp.json)}")
    
    # Test new releases
    resp = client.get('/api/beers/new')
    print(f"\nNew releases this week: {len(resp.json)}")
    for b in resp.json:
        print(f"  - {b['name']} ({b['style']})")
