from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random


class Expense(models.Model):
    """Model to track daily expenses."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    category = models.CharField(max_length=50, default='General')
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ₹{self.amount} ({self.date})"


class UserProfile(models.Model):
    """Extended user profile with gamification data."""
    THEME_CHOICES = [
        ('dark', 'Dark Mode'),
        ('light', 'Light Mode'),
        ('neon', 'Neon Glow'),
        ('midnight', 'Midnight Blue'),
        ('forest', 'Forest Green'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # XP and Leveling
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    
    # Streaks
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_expense_date = models.DateField(null=True, blank=True)
    streak_multiplier = models.FloatField(default=1.0)
    
    # Customization (unlockable)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default='dark')
    unlocked_themes = models.JSONField(default=list)
    unlocked_insights = models.JSONField(default=list)
    
    # Stats
    total_saved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    challenges_completed = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_rank(self):
        """Get rank based on level."""
        ranks = {
            1: "Budget Beginner",
            2: "Penny Tracker", 
            3: "Money Manager",
            4: "Finance Wizard",
            5: "Expense Master",
            6: "Budget Guru",
            7: "Wealth Warrior",
            8: "Fortune Keeper",
            9: "Money Legend",
            10: "Financial Titan"
        }
        return ranks.get(min(self.level, 10), "Financial Titan")
    
    def get_xp_for_next_level(self):
        """XP required to reach next level."""
        return self.level * 100
    
    def get_progress_percentage(self):
        """Progress to next level as percentage."""
        xp_needed = self.get_xp_for_next_level()
        current_level_xp = (self.level - 1) * 100
        xp_in_level = self.xp - (sum(range(1, self.level)) * 100)
        return min(int((xp_in_level / xp_needed) * 100), 100)
    
    def add_xp(self, amount):
        """Add XP with streak multiplier and check for level up."""
        xp_gained = int(amount * self.streak_multiplier)
        self.xp += xp_gained
        
        # Check for level up
        while self.xp >= sum(range(1, self.level + 1)) * 100:
            self.level += 1
            self.unlock_rewards()
        
        self.save()
        return xp_gained
    
    def update_streak(self):
        """Update streak based on expense activity."""
        today = timezone.now().date()
        
        if self.last_expense_date is None:
            self.current_streak = 1
        elif self.last_expense_date == today:
            return  # Already logged today
        elif self.last_expense_date == today - timedelta(days=1):
            self.current_streak += 1
            # Increase multiplier every 7 days (max 2.5x)
            self.streak_multiplier = min(1.0 + (self.current_streak // 7) * 0.25, 2.5)
        else:
            self.current_streak = 1
            self.streak_multiplier = 1.0
        
        self.last_expense_date = today
        self.longest_streak = max(self.longest_streak, self.current_streak)
        self.save()
    
    def unlock_rewards(self):
        """Unlock themes and insights based on level."""
        level_rewards = {
            2: {'theme': 'light', 'insight': 'weekly_summary'},
            3: {'theme': 'neon', 'insight': 'category_breakdown'},
            4: {'theme': 'midnight', 'insight': 'spending_forecast'},
            5: {'theme': 'forest', 'insight': 'savings_tips'},
        }
        
        if self.level in level_rewards:
            reward = level_rewards[self.level]
            if reward['theme'] not in self.unlocked_themes:
                self.unlocked_themes.append(reward['theme'])
            if reward['insight'] not in self.unlocked_insights:
                self.unlocked_insights.append(reward['insight'])
        
        self.save()
    
    def __str__(self):
        return f"Profile: Level {self.level} - {self.xp} XP"


class Achievement(models.Model):
    """Achievement/Badge definitions."""
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
        ('diamond', 'Diamond'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🏆')  # Emoji icon
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='bronze')
    xp_reward = models.IntegerField(default=50)
    
    # Unlock conditions (stored as JSON)
    condition_type = models.CharField(max_length=50)  # e.g., 'expense_count', 'streak', 'savings'
    condition_value = models.IntegerField()
    
    def __str__(self):
        return f"{self.icon} {self.name} ({self.tier})"


class UserAchievement(models.Model):
    """Tracks which achievements users have earned."""
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user_profile', 'achievement']


class Challenge(models.Model):
    """Daily/Weekly challenges."""
    CHALLENGE_TYPE = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    
    CATEGORY_CHOICES = [
        ('no_spend', 'No Spend'),
        ('budget', 'Stay Under Budget'),
        ('track', 'Track Expenses'),
        ('save', 'Save Money'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=10, default='🎯')
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Conditions
    target_value = models.IntegerField(default=0)  # e.g., max spend amount, min savings
    excluded_categories = models.JSONField(default=list)  # Categories to avoid
    
    # Rewards
    xp_reward = models.IntegerField(default=25)
    streak_bonus = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.icon} {self.title} ({self.challenge_type})"


class UserChallenge(models.Model):
    """Tracks user participation in challenges."""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='challenges')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress = models.IntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user_profile', 'challenge', 'started_at']


class LeaderboardEntry(models.Model):
    """Weekly/Monthly leaderboard entries."""
    PERIOD_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('alltime', 'All Time'),
    ]
    
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    period_type = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField()
    
    # Metrics
    xp_earned = models.IntegerField(default=0)
    challenges_completed = models.IntegerField(default=0)
    achievements_earned = models.IntegerField(default=0)
    savings_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    rank = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-xp_earned']
        unique_together = ['user_profile', 'period_type', 'period_start']
