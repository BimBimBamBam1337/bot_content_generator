import pandas as pd

from src.database.models import User, Subscription


class Excel:
    def __init__(self):
        self.name = "Статистика"
        self.df = pd.DataFrame()

    def create_df(self, users: list[User], subscriptions: list[Subscription]):
        subs_data = [
            {
                "user_id": sub.user_id,
                "cost": sub.cost or 0,
                "activated_at": sub.activated_at,
            }
            for sub in subscriptions
        ]
        subs_df = pd.DataFrame(subs_data)

        if not subs_df.empty:
            stats_df = subs_df.groupby("user_id").agg(
                total_cost=("cost", "sum"),
                activations=(
                    "activated_at",
                    lambda x: [d.strftime("%d.%m.%Y") for d in sorted(x)],
                ),
            )
        else:
            stats_df = pd.DataFrame(columns=["total_cost", "activations"])

        users_data = []
        for user in users:
            total_cost = (
                stats_df.loc[user.id, "total_cost"] if user.id in stats_df.index else 0
            )
            activations = (
                ", ".join(stats_df.loc[user.id, "activations"])
                if user.id in stats_df.index
                else ""
            )
            users_data.append(
                {
                    "Имя": getattr(user, "name", "") or "",
                    "Тэг": user.username or "",
                    "Потраченная сумма": total_cost,
                    "Даты активаций": activations,
                }
            )

        self.df = pd.DataFrame(users_data)

    def save(self, filename: str = "statistic.xlsx"):
        self.df.to_excel(filename, index=False)
