from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    Expense, UserProfile, Achievement, UserAchievement,
    Challenge, UserChallenge, LeaderboardEntry
)


def get_or_create_profile():
    """Get or create a default user profile (for demo without auth)."""
    profile, created = UserProfile.objects.get_or_create(
        user=None,
        defaults={
            'unlocked_themes': ['dark'],
            'unlocked_insights': []
        }
    )
    if created:
        create_default_achievements()
        create_default_challenges()
    return profile


def create_default_achievements():
    """Create default achievements if they don't exist."""
    achievements = [
        # Bronze Tier
        {'name': 'First Steps', 'description': 'Log your first expense', 'icon': '👣', 
         'tier': 'bronze', 'xp_reward': 25, 'condition_type': 'expense_count', 'condition_value': 1},
        {'name': 'Getting Started', 'description': 'Log 10 expenses', 'icon': '🌱', 
         'tier': 'bronze', 'xp_reward': 50, 'condition_type': 'expense_count', 'condition_value': 10},
        {'name': 'Streak Starter', 'description': 'Maintain a 3-day streak', 'icon': '🔥', 
         'tier': 'bronze', 'xp_reward': 50, 'condition_type': 'streak', 'condition_value': 3},
        
        # Silver Tier
        {'name': 'Consistent Tracker', 'description': 'Log 50 expenses', 'icon': '📊', 
         'tier': 'silver', 'xp_reward': 100, 'condition_type': 'expense_count', 'condition_value': 50},
        {'name': 'Week Warrior', 'description': 'Maintain a 7-day streak', 'icon': '⚔️', 
         'tier': 'silver', 'xp_reward': 100, 'condition_type': 'streak', 'condition_value': 7},
        {'name': 'Challenge Accepted', 'description': 'Complete 5 challenges', 'icon': '🎯', 
         'tier': 'silver', 'xp_reward': 100, 'condition_type': 'challenges', 'condition_value': 5},
        
        # Gold Tier
        {'name': 'Century Club', 'description': 'Log 100 expenses', 'icon': '💯', 
         'tier': 'gold', 'xp_reward': 200, 'condition_type': 'expense_count', 'condition_value': 100},
        {'name': 'Fortnight Fighter', 'description': 'Maintain a 14-day streak', 'icon': '🛡️', 
         'tier': 'gold', 'xp_reward': 200, 'condition_type': 'streak', 'condition_value': 14},
        {'name': 'Challenge Champion', 'description': 'Complete 15 challenges', 'icon': '🏅', 
         'tier': 'gold', 'xp_reward': 200, 'condition_type': 'challenges', 'condition_value': 15},
        
        # Platinum Tier
        {'name': 'Expense Expert', 'description': 'Log 250 expenses', 'icon': '🎓', 
         'tier': 'platinum', 'xp_reward': 350, 'condition_type': 'expense_count', 'condition_value': 250},
        {'name': 'Month Master', 'description': 'Maintain a 30-day streak', 'icon': '🌙', 
         'tier': 'platinum', 'xp_reward': 350, 'condition_type': 'streak', 'condition_value': 30},
        
        # Diamond Tier
        {'name': 'Financial Legend', 'description': 'Log 500 expenses', 'icon': '👑', 
         'tier': 'diamond', 'xp_reward': 500, 'condition_type': 'expense_count', 'condition_value': 500},
        {'name': 'Streak Immortal', 'description': 'Maintain a 60-day streak', 'icon': '💎', 
         'tier': 'diamond', 'xp_reward': 500, 'condition_type': 'streak', 'condition_value': 60},
    ]
    
    for ach in achievements:
        Achievement.objects.get_or_create(name=ach['name'], defaults=ach)


def create_default_challenges():
    """Create default challenges if they don't exist."""
    challenges = [
        # Daily Challenges
        {'title': 'No Dining Out Today', 'description': 'Avoid restaurant expenses for 24 hours',
         'icon': '🍽️', 'challenge_type': 'daily', 'category': 'no_spend', 
         'target_value': 0, 'xp_reward': 30, 'excluded_categories': ['Food', 'Dining', 'Restaurant']},
        {'title': 'Minimalist Monday', 'description': 'Spend less than ₹500 today',
         'icon': '💰', 'challenge_type': 'daily', 'category': 'budget', 
         'target_value': 500, 'xp_reward': 35},
        {'title': 'Track Everything', 'description': 'Log at least 3 expenses today',
         'icon': '📝', 'challenge_type': 'daily', 'category': 'track', 
         'target_value': 3, 'xp_reward': 25},
        {'title': 'No Impulse Day', 'description': 'No shopping/entertainment expenses',
         'icon': '🛒', 'challenge_type': 'daily', 'category': 'no_spend', 
         'target_value': 0, 'xp_reward': 40, 'excluded_categories': ['Shopping', 'Entertainment']},
         
        # Weekly Challenges
        {'title': 'Frugal Week', 'description': 'Keep weekly spending under ₹5000',
         'icon': '📉', 'challenge_type': 'weekly', 'category': 'budget', 
         'target_value': 5000, 'xp_reward': 100},
        {'title': 'Tracking Champion', 'description': 'Log expenses every day this week',
         'icon': '🏆', 'challenge_type': 'weekly', 'category': 'track', 
         'target_value': 7, 'xp_reward': 150, 'streak_bonus': True},
        {'title': 'Home Cook Hero', 'description': 'No dining out for a week',
         'icon': '👨‍🍳', 'challenge_type': 'weekly', 'category': 'no_spend', 
         'target_value': 0, 'xp_reward': 200, 'excluded_categories': ['Food', 'Dining', 'Restaurant']},
        {'title': 'Savings Sprint', 'description': 'Save at least ₹1000 this week',
         'icon': '🏃', 'challenge_type': 'weekly', 'category': 'save', 
         'target_value': 1000, 'xp_reward': 175},
    ]
    
    for ch in challenges:
        excluded = ch.pop('excluded_categories', [])
        Challenge.objects.get_or_create(
            title=ch['title'], 
            defaults={**ch, 'excluded_categories': excluded}
        )


def check_achievements(profile):
    """Check and award any newly earned achievements."""
    expense_count = Expense.objects.count()
    earned_achievements = []
    
    for achievement in Achievement.objects.all():
        # Skip if already earned
        if UserAchievement.objects.filter(user_profile=profile, achievement=achievement).exists():
            continue
        
        earned = False
        if achievement.condition_type == 'expense_count':
            earned = expense_count >= achievement.condition_value
        elif achievement.condition_type == 'streak':
            earned = profile.current_streak >= achievement.condition_value
        elif achievement.condition_type == 'challenges':
            earned = profile.challenges_completed >= achievement.condition_value
        
        if earned:
            UserAchievement.objects.create(user_profile=profile, achievement=achievement)
            profile.add_xp(achievement.xp_reward)
            earned_achievements.append(achievement)
    
    return earned_achievements


def add_expense(request):
    """View to add a new expense."""
    profile = get_or_create_profile()
    
    if request.method == "POST":
        amount = request.POST.get("amount")
        description = request.POST.get("description")
        date = request.POST.get("date")
        category = request.POST.get("category", "General")

        Expense.objects.create(
            amount=amount,
            description=description,
            date=date,
            category=category
        )
        
        # Update streak and add XP
        profile.update_streak()
        xp_gained = profile.add_xp(10)  # Base 10 XP per expense
        
        # Check for new achievements
        check_achievements(profile)
        
        # Update active challenge progress
        update_challenge_progress(profile)

        return redirect("expense_list")

    expenses = Expense.objects.all()
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Get active challenges
    active_challenges = UserChallenge.objects.filter(
        user_profile=profile, 
        status='active'
    ).select_related('challenge')[:3]
    
    context = {
        'profile': profile,
        'total_expenses': expenses.count(),
        'total_amount': int(total_amount),
        'active_challenges': active_challenges,
        'categories': ['General', 'Food', 'Transport', 'Shopping', 'Entertainment', 'Bills', 'Health', 'Other'],
    }
    
    return render(request, "add_expense.html", context)


def expense_list(request):
    """View to display all expenses."""
    profile = get_or_create_profile()
    expenses = Expense.objects.all()
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Calculate stats
    unique_dates = expenses.values('date').distinct().count()
    avg_daily = int(total_amount / unique_dates) if unique_dates > 0 else 0
    
    # Check for new achievements
    new_achievements = check_achievements(profile)
    
    # Recent achievements
    recent_achievements = UserAchievement.objects.filter(
        user_profile=profile
    ).select_related('achievement').order_by('-earned_at')[:3]
    
    context = {
        'profile': profile,
        'expenses': expenses,
        'total_amount': int(total_amount),
        'avg_daily': avg_daily,
        'new_achievements': new_achievements,
        'recent_achievements': recent_achievements,
    }
    
    return render(request, "expense_list.html", context)


def dashboard(request):
    """Main gamification dashboard."""
    profile = get_or_create_profile()
    expenses = Expense.objects.all()
    
    # Stats
    total_amount = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    this_week = expenses.filter(date__gte=timezone.now().date() - timedelta(days=7))
    week_amount = this_week.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Achievements
    earned_count = UserAchievement.objects.filter(user_profile=profile).count()
    total_achievements = Achievement.objects.count()
    
    # Active challenges
    active_challenges = UserChallenge.objects.filter(
        user_profile=profile, 
        status='active'
    ).select_related('challenge')
    
    # Recent activity
    recent_expenses = expenses[:5]
    
    context = {
        'profile': profile,
        'total_expenses': expenses.count(),
        'total_amount': int(total_amount),
        'week_amount': int(week_amount),
        'earned_achievements': earned_count,
        'total_achievements': total_achievements,
        'active_challenges': active_challenges,
        'recent_expenses': recent_expenses,
    }
    
    return render(request, "dashboard.html", context)


def challenges_view(request):
    """View all challenges and progress."""
    profile = get_or_create_profile()
    
    # Get or assign daily challenges
    daily_challenges = get_daily_challenges(profile)
    weekly_challenges = get_weekly_challenges(profile)
    
    # Completed challenges
    completed = UserChallenge.objects.filter(
        user_profile=profile,
        status='completed'
    ).select_related('challenge').order_by('-completed_at')[:10]
    
    context = {
        'profile': profile,
        'daily_challenges': daily_challenges,
        'weekly_challenges': weekly_challenges,
        'completed_challenges': completed,
    }
    
    return render(request, "challenges.html", context)


def get_daily_challenges(profile):
    """Get today's active daily challenges."""
    today = timezone.now().date()
    
    # Check if user has active daily challenges for today
    active = UserChallenge.objects.filter(
        user_profile=profile,
        challenge__challenge_type='daily',
        started_at__date=today,
        status='active'
    ).select_related('challenge')
    
    if not active.exists():
        # Assign new daily challenges
        daily = Challenge.objects.filter(challenge_type='daily', is_active=True)[:2]
        for challenge in daily:
            UserChallenge.objects.create(
                user_profile=profile,
                challenge=challenge,
                status='active'
            )
        active = UserChallenge.objects.filter(
            user_profile=profile,
            challenge__challenge_type='daily',
            started_at__date=today
        ).select_related('challenge')
    
    return active


def get_weekly_challenges(profile):
    """Get this week's active weekly challenges."""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    active = UserChallenge.objects.filter(
        user_profile=profile,
        challenge__challenge_type='weekly',
        started_at__date__gte=week_start,
        status='active'
    ).select_related('challenge')
    
    if not active.exists():
        weekly = Challenge.objects.filter(challenge_type='weekly', is_active=True)[:2]
        for challenge in weekly:
            UserChallenge.objects.create(
                user_profile=profile,
                challenge=challenge,
                status='active'
            )
        active = UserChallenge.objects.filter(
            user_profile=profile,
            challenge__challenge_type='weekly',
            started_at__date__gte=week_start
        ).select_related('challenge')
    
    return active


def update_challenge_progress(profile):
    """Update progress on active challenges after expense is logged."""
    today = timezone.now().date()
    active_challenges = UserChallenge.objects.filter(
        user_profile=profile,
        status='active'
    ).select_related('challenge')
    
    for uc in active_challenges:
        challenge = uc.challenge
        
        if challenge.category == 'track':
            # Count expenses logged
            if challenge.challenge_type == 'daily':
                count = Expense.objects.filter(date=today).count()
            else:
                week_start = today - timedelta(days=today.weekday())
                count = Expense.objects.filter(date__gte=week_start).values('date').distinct().count()
            
            uc.progress = count
            if count >= challenge.target_value:
                complete_challenge(uc, profile)
        
        uc.save()


def complete_challenge(user_challenge, profile):
    """Mark a challenge as completed and award XP."""
    user_challenge.status = 'completed'
    user_challenge.completed_at = timezone.now()
    user_challenge.save()
    
    # Award XP with streak bonus if applicable
    xp = user_challenge.challenge.xp_reward
    if user_challenge.challenge.streak_bonus:
        xp = int(xp * profile.streak_multiplier)
    
    profile.add_xp(xp)
    profile.challenges_completed += 1
    profile.save()


def achievements_view(request):
    """View all achievements and badges."""
    profile = get_or_create_profile()
    
    # Get all achievements grouped by tier
    all_achievements = Achievement.objects.all().order_by('tier', 'condition_value')
    earned_ids = UserAchievement.objects.filter(
        user_profile=profile
    ).values_list('achievement_id', flat=True)
    
    # Group by tier
    tiers = ['bronze', 'silver', 'gold', 'platinum', 'diamond']
    achievements_by_tier = {}
    for tier in tiers:
        achievements_by_tier[tier] = [
            {
                'achievement': a,
                'earned': a.id in earned_ids,
                'progress': get_achievement_progress(profile, a)
            }
            for a in all_achievements.filter(tier=tier)
        ]
    
    context = {
        'profile': profile,
        'achievements_by_tier': achievements_by_tier,
        'earned_count': len(earned_ids),
        'total_count': all_achievements.count(),
    }
    
    return render(request, "achievements.html", context)


def get_achievement_progress(profile, achievement):
    """Calculate progress towards an achievement."""
    if achievement.condition_type == 'expense_count':
        current = Expense.objects.count()
    elif achievement.condition_type == 'streak':
        current = profile.current_streak
    elif achievement.condition_type == 'challenges':
        current = profile.challenges_completed
    else:
        current = 0
    
    return min(int((current / achievement.condition_value) * 100), 100)


def leaderboard_view(request):
    """View leaderboard rankings."""
    profile = get_or_create_profile()
    
    # For demo, create simulated leaderboard entries
    # In production, this would show real user data
    leaderboard_data = [
        {'rank': 1, 'name': 'FinanceGuru', 'xp': 2450, 'level': 8, 'streak': 45},
        {'rank': 2, 'name': 'BudgetBoss', 'xp': 1890, 'level': 6, 'streak': 30},
        {'rank': 3, 'name': 'SavingsKing', 'xp': 1650, 'level': 5, 'streak': 21},
        {'rank': 4, 'name': 'You', 'xp': profile.xp, 'level': profile.level, 'streak': profile.current_streak, 'is_current': True},
        {'rank': 5, 'name': 'MoneyMaster', 'xp': max(profile.xp - 100, 0), 'level': max(profile.level - 1, 1), 'streak': 7},
    ]
    
    # Sort by XP
    leaderboard_data.sort(key=lambda x: x['xp'], reverse=True)
    for i, entry in enumerate(leaderboard_data):
        entry['rank'] = i + 1
    
    context = {
        'profile': profile,
        'leaderboard': leaderboard_data,
        'period': 'weekly',
    }
    
    return render(request, "leaderboard.html", context)


def settings_view(request):
    """User settings including theme selection."""
    profile = get_or_create_profile()
    
    if request.method == "POST":
        theme = request.POST.get("theme")
        if theme in profile.unlocked_themes or theme == 'dark':
            profile.theme = theme
            profile.save()
        return redirect("settings")
    
    all_themes = [
        {'id': 'dark', 'name': 'Dark Mode', 'icon': '🌙'},
        {'id': 'light', 'name': 'Light Mode', 'icon': '☀️'},
        {'id': 'neon', 'name': 'Neon Glow', 'icon': '💜'},
        {'id': 'midnight', 'name': 'Midnight Blue', 'icon': '🌌'},
        {'id': 'forest', 'name': 'Forest Green', 'icon': '🌲'},
    ]
    
    for theme in all_themes:
        theme['unlocked'] = theme['id'] in profile.unlocked_themes or theme['id'] == 'dark'
    
    context = {
        'profile': profile,
        'themes': all_themes,
    }
    
    return render(request, "settings.html", context)


def predictions_view(request):
    """Future You - Spending predictions and savings projections."""
    profile = get_or_create_profile()
    expenses = Expense.objects.all()
    today = timezone.now().date()
    
    # Get user's monthly income/budget (default or from request)
    monthly_income = int(request.GET.get('income', 50000))
    
    # Calculate spending patterns
    total_expenses = expenses.count()
    total_amount = float(expenses.aggregate(Sum('amount'))['amount__sum'] or 0)
    
    # Get expenses from last 30 days for better accuracy
    last_30_days = expenses.filter(date__gte=today - timedelta(days=30))
    last_30_amount = float(last_30_days.aggregate(Sum('amount'))['amount__sum'] or 0)
    
    # Calculate daily and monthly averages
    days_tracked = max((today - expenses.order_by('date').first().date).days, 1) if expenses.exists() else 1
    days_in_last_30 = min(days_tracked, 30)
    
    daily_avg = last_30_amount / days_in_last_30 if days_in_last_30 > 0 else 0
    monthly_avg = daily_avg * 30
    
    # Calculate projected values
    days_left_this_month = 30 - today.day
    projected_month_spend = (total_amount if days_tracked < 30 else last_30_amount) + (daily_avg * days_left_this_month)
    
    # Calculate savings
    monthly_savings = monthly_income - monthly_avg
    yearly_savings = monthly_savings * 12
    
    # Savings scenarios
    scenarios = [
        {
            'name': 'Current Path',
            'icon': '📊',
            'monthly_save': int(monthly_savings),
            'yearly_save': int(yearly_savings),
            'color': 'blue' if monthly_savings >= 0 else 'red',
            'description': 'If you continue spending at this rate'
        },
        {
            'name': 'Cut 10%',
            'icon': '✂️',
            'monthly_save': int(monthly_income - (monthly_avg * 0.9)),
            'yearly_save': int((monthly_income - (monthly_avg * 0.9)) * 12),
            'color': 'green',
            'description': 'Reduce spending by 10%'
        },
        {
            'name': 'Cut 25%',
            'icon': '🎯',
            'monthly_save': int(monthly_income - (monthly_avg * 0.75)),
            'yearly_save': int((monthly_income - (monthly_avg * 0.75)) * 12),
            'color': 'gold',
            'description': 'Reduce spending by 25%'
        },
    ]
    
    # Monthly projections for the year
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    current_month = today.month
    
    monthly_projections = []
    cumulative_savings = 0
    for i in range(12):
        month_index = (current_month - 1 + i) % 12
        cumulative_savings += monthly_savings
        monthly_projections.append({
            'month': months[month_index],
            'savings': int(cumulative_savings),
            'spending': int(monthly_avg),
            'is_current': i == 0,
            'percentage': min(int((cumulative_savings / (yearly_savings if yearly_savings > 0 else 1)) * 100), 100) if yearly_savings > 0 else 0
        })
    
    # Category breakdown for insights
    category_spending = expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    top_category = category_spending[0] if category_spending else {'category': 'None', 'total': 0}
    
    # Financial health score (0-100)
    savings_rate = (monthly_savings / monthly_income * 100) if monthly_income > 0 else 0
    if savings_rate >= 30:
        health_score = 95
        health_status = 'Excellent'
        health_color = 'green'
    elif savings_rate >= 20:
        health_score = 80
        health_status = 'Great'
        health_color = 'green'
    elif savings_rate >= 10:
        health_score = 65
        health_status = 'Good'
        health_color = 'yellow'
    elif savings_rate >= 0:
        health_score = 45
        health_status = 'Fair'
        health_color = 'orange'
    else:
        health_score = 25
        health_status = 'Needs Attention'
        health_color = 'red'
    
    # Motivational insights
    insights = []
    if monthly_savings > 0:
        insights.append({
            'icon': '🎉',
            'text': f"You're saving ₹{int(monthly_savings):,}/month - that's ₹{int(yearly_savings):,} per year!",
            'type': 'positive'
        })
    else:
        insights.append({
            'icon': '⚠️',
            'text': f"You're overspending by ₹{int(abs(monthly_savings)):,}/month",
            'type': 'warning'
        })
    
    if top_category['total'] > 0:
        insights.append({
            'icon': '💡',
            'text': f"Your biggest expense category is {top_category['category']} (₹{int(top_category['total']):,})",
            'type': 'info'
        })
    
    # Future milestones
    milestones = []
    if yearly_savings > 0:
        milestone_targets = [10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        for target in milestone_targets:
            if target > yearly_savings:
                months_needed = target / monthly_savings if monthly_savings > 0 else 999
                if months_needed <= 36:
                    milestones.append({
                        'amount': target,
                        'months': int(months_needed),
                        'label': f"₹{target:,}"
                    })
                if len(milestones) >= 3:
                    break
    
    context = {
        'profile': profile,
        'monthly_income': monthly_income,
        'daily_avg': int(daily_avg),
        'monthly_avg': int(monthly_avg),
        'monthly_savings': int(monthly_savings),
        'yearly_savings': int(yearly_savings),
        'savings_rate': int(savings_rate),
        'scenarios': scenarios,
        'monthly_projections': monthly_projections,
        'health_score': health_score,
        'health_status': health_status,
        'health_color': health_color,
        'insights': insights,
        'milestones': milestones,
        'category_spending': category_spending,
    }
    
    return render(request, "predictions.html", context)

