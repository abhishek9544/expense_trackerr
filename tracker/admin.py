from django.contrib import admin
from .models import (
    Expense, UserProfile, Achievement, UserAchievement,
    Challenge, UserChallenge, LeaderboardEntry
)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'category', 'date', 'created_at')
    list_filter = ('category', 'date')
    search_fields = ('description',)
    ordering = ('-date',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'xp', 'current_streak', 'streak_multiplier')
    list_filter = ('level', 'theme')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'xp_reward', 'condition_type', 'condition_value')
    list_filter = ('tier',)
    ordering = ('tier', 'condition_value')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'achievement', 'earned_at')
    list_filter = ('achievement__tier',)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'challenge_type', 'category', 'xp_reward', 'is_active')
    list_filter = ('challenge_type', 'category', 'is_active')


@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'challenge', 'status', 'progress', 'started_at')
    list_filter = ('status', 'challenge__challenge_type')


@admin.register(LeaderboardEntry)
class LeaderboardEntryAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'period_type', 'rank', 'xp_earned')
    list_filter = ('period_type',)
    ordering = ('rank',)
