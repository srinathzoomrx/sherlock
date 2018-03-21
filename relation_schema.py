rel_schema = {
    'stadiums': [{
        'type': "R",
        'related': {
            "matches": "stadiums.id = matches.stadium_id"
        }
    }],
    'matches': [{
        'type': "R",
        'related': {
            "innings": "matches.id = innings.match_id",
            "stadiums": "matches.stadium_id = stadiums.id",
            "players": "matches.player_of_the_match = players.name",
            "teams": ["matches.team1_id = teams.id", "matches.team2_id = teams.id"],
            "batsman": "matches.id = batsman.matches_id",
            "bowler": "matches.id = bowler.matches_id"
        }
    }],
    'games': [{
        'type': "R",
        'relation': 'matches',
        'related': {
            "innings": "matches.id = innings.match_id",
            "stadiums": "matches.stadium_id = stadiums.id",
            "players": "matches.player_of_the_match = players.name",
            "teams": ["matches.team1_id = teams.id", "matches.team2_id = teams.id"],
            "batsman": "matches.id = batsman.matches_id",
            "bowler": "matches.id = bowler.matches_id"
        }
    }],
    'players': [{
        'type': "R",
        'related': {
            "matches": "players.name = matches.player_of_the_match",
            "overs": "players.name = overs.bowler",
            "balls": "players.id = balls.batsman_id",
            "teams": "players.teamid = teams.id",
            "wickets": "players.id = wickets.player_out_id",
            "batsman": "players.id = batsman.matches_id",
            "bowler": "players.id = bowler.matches_id"
        }
    }],
    'player': [{
        'type': "R",
        'relation': "players",
        'related': {
            "matches": "players.name = matches.player_of_the_match",
            "overs": "players.name = overs.bowler",
            "balls": "players.id = balls.batsman_id",
            "teams": "players.teamid = teams.id",
            "wickets": "players.id = wickets.player_out_id"
        }
    }],
    'innings': [{
        'type': "R",
        'related': {
            "matches": "innings.match_id = matches.id",
            "overs": "innings.id = overs.inning_id",
            "teams": ["innings.batting_team = teams.name", "innings.bowling_team = teams.name"]
        }
    }],
    'overs': [{
        'type': "R",
        'related': {
            "innings": "overs.inning_id = innings.id",
            "balls": "overs.id = balls.over_id",
            "players": "overs.bowler = players.name"
        }
    }],
    'balls': [{
        'type': "R",
        'related': {
            "overs": "balls.over_id = overs.id",
            "players": "balls.batsman_id = players.id",
            "wickets": "balls.id = wickets.ball_id"
        }
    }],
    'teams': [{
        'type': "R",
        'related': {
            "matches": ["teams.id = matches.team1_id", "teams.id = matches.team2_id"],
            "players": "teams.id = players.teamid",
            "innings": ["teams.name = innings.batting_team", "teams.name = innings.bowling_team"]
        }
    }],
    'wickets': [{
        'type': "R",
        'related': {
            "balls": "wickets.ball_id = balls.id",
            "players": "wickets.player_out_id = players.id",
        }
    }],
    'batsman': [{
        'type': "R",
        'related': {
            "matches": "batsman.matches_id = matches.id",
            "players": "batsman.player_id = players.id"
        }
    }],
    'bowler': [{
        'type': "R",
        'related': {
            "matches": "bowler.matches_id = matches.id",
            "players": "bowler.player_id = players.id"
        }
    }]
}
