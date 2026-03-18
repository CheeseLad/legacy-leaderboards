from django.urls import path
from .views import (
    WriteStatsView,
    TopRankView,
    FriendsLeaderboardView,
    MyScoreView,
    LeaderboardView,
)

urlpatterns = [
    path("api/leaderboard/write/", WriteStatsView.as_view()),
    path("api/leaderboard/top/", TopRankView.as_view()),
    path("api/leaderboard/friends/", FriendsLeaderboardView.as_view()),
    path("api/leaderboard/my-score/", MyScoreView.as_view()),
    path("api/leaderboard/", LeaderboardView.as_view()),
]