import discord
from discord.ext import commands
from discord import app_commands
import json
import random
import string
from dotenv import load_dotenv
from discord.ui import View, Button, Select, Modal, TextInput
import uuid, datetime
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
import os
os.system("playwright install --with-deps")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from discord.ext import tasks
app = FastAPI()
from dotenv import load_dotenv

CAMPAIGN_UPDATES_CHANNEL = "campaign-updates"  # Channel für globale Updates
CAMPAIGN_RESPONSES_FILE = os.path.join(BASE_DIR, "campaign_responses.json")

def load_json(filename):
    full_path = os.path.join("campaign-ui", "campaign-ui", filename)
    if not os.path.exists(full_path):
        return {}
    with open(full_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename, data):
    full_path = os.path.join("campaign-ui", "campaign-ui", filename)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_submissions():
    with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
        return json.load(f)

def load_campaign_responses():
    try:
        with open("campaign-ui/campaign-ui/campaign_responses.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_submission_by_id(submissions, user_id):
    for sub in submissions:
        if sub["id"] == user_id:
            return sub
    return None

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.temp_submissions = {}
verification_codes = {}

def make_creator_callback(creator_id, creator_name):
    async def button_callback(interaction: discord.Interaction):
        if "selected_creators" not in bot.temp_campaign_data:
            bot.temp_campaign_data["selected_creators"] = []
        bot.temp_campaign_data["selected_creators"].append(creator_id)
        await interaction.response.send_message(
            f"✅ {creator_name} wurde zur Campaign hinzugefügt!",
            ephemeral=True
        )
    return button_callback

class CreatorGridView(discord.ui.View):
    def __init__(self, creators, per_page=30):
        super().__init__(timeout=300)
        self.creators = creators
        self.per_page = per_page
        self.page = 0
        self.selected_creators = set()
        self.render_page()

    def render_page(self):
        self.clear_items()
        start = self.page * self.per_page
        end = start + self.per_page
        current_creators = self.creators[start:end]

        for i, creator in enumerate(current_creators):
            label = f"{creator['username']} ({creator['platform']})"
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, row=i % 5)

            async def callback(interaction, creator_id=creator["user_id"]):
                self.selected_creators.add(creator_id)
                await interaction.response.send_message(f"✅ `{creator_id}` zur Kampagne hinzugefügt!", ephemeral=True)

            button.callback = callback
            self.add_item(button)

        # Navigationsbuttons
        if self.page > 0:
            self.add_item(discord.ui.Button(label="⬅️ Zurück", custom_id="prev", style=discord.ButtonStyle.primary))
        if end < len(self.creators):
            self.add_item(discord.ui.Button(label="➡️ Weiter", custom_id="next", style=discord.ButtonStyle.primary))

        # Finalize-Button
        self.add_item(discord.ui.Button(label="✅ Campaign erstellen", custom_id="finalize", style=discord.ButtonStyle.success))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # Jeder darf Buttons klicken

    async def on_timeout(self):
        self.clear_items()

class CreatorSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(
            placeholder="Wähle Creator aus...",
            min_values=1,
            max_values=len(options),
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        view: CreatorPageView = self.view  # type: ignore
        view.selected.update(self.values)
        await interaction.response.send_message(
            f"✅ {len(self.values)} hinzugefügt – insgesamt {len(view.selected)}",
            ephemeral=True
        )

class NavButton(discord.ui.Button):
    def __init__(self, label, new_page):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.new_page = new_page

    async def callback(self, interaction: discord.Interaction):
        view: CreatorPageView = self.view  # type: ignore
        await interaction.response.edit_message(
            content="🎯 Wähle Creator:",
            view=CreatorPageView(view.creators, self.new_page, view.selected)
        )

import math
from typing import List, Dict, Optional

import discord

__all__ = ["CreatorPageView"]


class CreatorPageView(discord.ui.View):
    """A reusable Discord UI view that paginates a list of creators, handles
    navigation, and exposes a callback to start the campaign‑creation flow.

    Parameters
    ----------
    creators: List[Dict]
        A list of creator dictionaries coming from your DB / API. Each dict *should* contain
        at least a ``name`` field and *ideally* a ``user_id``. If ``user_id`` is missing we
        fallback to the creator's list‑index so the UI never breaks in tests.
    page_size: int, optional
        How many creators to show per page (default ``6``).
    timeout: Optional[float]
        Passed to ``discord.ui.View`` so the entire view can time‑out (default "None" → never).
    """

    def __init__(
        self,
        creators: List[Dict],
        *,
        page_size: int = 6,
        timeout: Optional[float] = 180,
    ) -> None:
        super().__init__(timeout=timeout)

        # ‑‑ Core state --------------------------------------------------
        self.creators: List[Dict] = creators
        self.page_size = max(1, page_size)
        self.page_index: int = 0  # zero‑based
        self.selected_creator: Optional[Dict] = None

        # ‑‑ Derived -----------------------------------------------------
        self.total_pages: int = math.ceil(len(self.creators) / self.page_size)

        # Initial render
        self._refresh_buttons()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def get_current_page_creators(self) -> List[Dict]:
        start = self.page_index * self.page_size
        end = start + self.page_size
        return self.creators[start:end]

def generate_campaign_id():
    """Erstellt eine eindeutige Campaign-ID im Format CAMP-XXX"""
    from random import randint
    return f"CAMP-{randint(100, 999)}"

async def send_campaign_update(message: str):
    """Postet eine Update-Nachricht in den campaign-updates Channel."""
    if not bot.guilds:
        print("[WARN] Kein Guild gefunden (Bot evtl. nicht eingeloggt).")
        return
    guild = bot.guilds[0]

    channel = discord.utils.get(guild.text_channels, name=CAMPAIGN_UPDATES_CHANNEL)
    if channel:
        await channel.send(message)
    else:
        print(f"[WARN] Channel '{CAMPAIGN_UPDATES_CHANNEL}' nicht gefunden!")

async def update_creator_status(campaign_id, creator_name, status):
    """Aktualisiert den Status (accepted/declined) eines Creators und postet Update."""
    if not os.path.exists(CAMPAIGN_RESPONSES_FILE):
        return False

    with open(CAMPAIGN_RESPONSES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for campaign in data:
        if campaign["campaign_id"] == campaign_id:
            for creator in campaign["creators"]:
                if creator["name"] == creator_name:
                    creator["status"] = status
                    break

    with open(CAMPAIGN_RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # ---- NEU: Update im campaign-updates Channel ----
    await send_campaign_update(f"**{creator_name}** hat Kampagne **{campaign_id}** { '✅ akzeptiert' if status=='accepted' else '❌ abgelehnt'}.")

    return True

    # ---------------------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------------------
    def _refresh_buttons(self) -> None:
        """(Re)build all buttons for the current page and navigation."""
        # Clear any existing children first
        self.clear_items()

        # -- Creator buttons --------------------------------------------
        for idx, creator in enumerate(self.get_current_page_creators()):
            label = creator.get("name", f"Creator {idx + 1}")
            # Fallback key avoids KeyError in tests where ``user_id`` may be missing
            custom_id = str(creator.get("user_id", f"index:{idx + (self.page_index * self.page_size)}"))

            self.add_item(
                discord.ui.Button(
                    style=discord.ButtonStyle.primary,
                    label=label,
                    custom_id=f"creator:{custom_id}",
                )
            )

        # -- Navigation --------------------------------------------------
        nav_row = []
        if self.page_index > 0:
            nav_row.append(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="◀ Zurück",
                    custom_id="nav:prev",
                )
            )

        if (self.page_index + 1) < self.total_pages:
            nav_row.append(
                discord.ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="Weiter ▶",
                    custom_id="nav:next",
                )
            )

        for btn in nav_row:
            self.add_item(btn)

        # -- Finalize campaign ------------------------------------------
        # Only enable if a creator is selected
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.success,
                label="Campaign erstellen",
                custom_id="action:create_campaign",
                disabled=self.selected_creator is None,
            )
        )

    # ---------------------------------------------------------------------
    # Interaction dispatcher
    # ---------------------------------------------------------------------
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Intercept any component interaction and dispatch to proper handler."""
        cid = interaction.data.get("custom_id")
        if not cid:
            return False

        try:
            prefix, payload = cid.split(":", 1)
        except ValueError:
            # Not for us
            return False

        if prefix == "creator":
            await self._on_creator_click(interaction, payload)
        elif prefix == "nav":
            await self._on_nav(interaction, payload)
        elif prefix == "action":
            await self._on_action(interaction, payload)
        else:
            return False

        return True  # indicate we handled it

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    async def _on_creator_click(self, interaction: discord.Interaction, payload: str):
        """Handle clicks on creator buttons."""
        # Decode selection; fallback if we stored index instead of user_id
        if payload.startswith("index:"):
            index = int(payload.split(":", 1)[1])
            self.selected_creator = self.creators[index]
        else:
            # Regular case: find by user_id (string‑compare for robustness)
            self.selected_creator = next(
                (c for c in self.creators if str(c.get("user_id")) == payload),
                None,
            )

        # Refresh UI state (enable campaign button)
        self._refresh_buttons()
        await interaction.response.edit_message(view=self)

    async def _on_nav(self, interaction: discord.Interaction, direction: str):
        """Page navigation."""
        if direction == "next":
            self.page_index = min(self.page_index + 1, self.total_pages - 1)
        elif direction == "prev":
            self.page_index = max(self.page_index - 1, 0)

        self._refresh_buttons()
        await interaction.response.edit_message(view=self)

    async def _on_action(self, interaction: discord.Interaction, action: str):
        if action != "create_campaign":
            return

        if not self.selected_creator:
            # Should not happen due to disabled button but guard anyway
            await interaction.response.send_message(
                "❌ Bitte zuerst einen Creator auswählen.",
                ephemeral=True,
            )
            return

        # TODO: integrate with your main bot logic / DB
        # e.g. store selected_creator and move user to /finalize‑campaign flow
        await interaction.response.send_message(
            f"✅ Campaign‑Flow für {self.selected_creator.get('name', 'Unknown')} gestartet!",
            ephemeral=True,
        )

        # Optionally: disable the view now
        self.stop()

class CreatorInfoModal(Modal):
    def __init__(self, bot):
        super().__init__(title="Provide Additional Creator Info")
        self.bot = bot

        self.content_type = TextInput(
            label="Content Type (e.g. Gaming, Music, Reactions)",
            placeholder="Describe your content style...",
            required=True
        )
        self.monthly_views = TextInput(
            label="Views in the last 30 days",
            placeholder="e.g. 250,000",
            required=True
        )
        self.new_followers = TextInput(
            label="New Followers in the Last 30 Days",
            placeholder="e.g. 1200",
            required=True
        )
        self.price_info = TextInput(
            label="Price per Video or per 1000 Views",
            placeholder="e.g. €5 per post or €0,50 per 1.000 views",
            required=True
        )
        self.extra_offer = TextInput(
            label="Extra Offers (optional)",
            placeholder="e.g. Link in Bio, Product Reviews, etc.",
            required=False
        )

        self.add_item(self.content_type)
        self.add_item(self.monthly_views)
        self.add_item(self.new_followers)
        self.add_item(self.price_info)
        self.add_item(self.extra_offer)

    async def on_submit(self, interaction: discord.Interaction):
        user = interaction.user
        submission_info = self.bot.temp_submissions.get(user.id)

        if not submission_info:
            await interaction.response.send_message("⚠️ No submission data found. Please use `/verify` first.", ephemeral=True)
            return

        # Daten in temp speichern
        submission_info["details"] = {
            "views_last_30": self.monthly_views.value,
            "new_followers": self.new_followers.value,
            "price": self.price_info.value,
            "extra_offers": self.extra_offer.value,
            "content_type": self.content_type.value
        }

        # Nun final speichern
        try:
            with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
                submissions = json.load(f)
        except:
            submissions = []

        # Vorherige Einträge für diesen User + Plattform entfernen
        submissions = [
            s for s in submissions
            if not (s.get("user_id") == user.id and s.get("platform") == submission_info["platform"])
        ]

        submission = {
            "user_id": user.id,
            "username": user.name,
            "platform": submission_info["platform"],
            "handle": submission_info["username"],
            "bio": submission_info["bio"],
            "status": "pending",
            "code": submission_info["code"],
            "details": submission_info["details"]
        }

        submissions.append(submission)
        with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
            json.dump(submissions, f, indent=2)

        # Channel finden & bestätigen
        verify_channel = next((c for c in interaction.guild.text_channels if c.topic == submission_info["code"][1:]), None)
        if verify_channel:
            await verify_channel.send(
                f"{user.mention}, your application and additional info were submitted successfully.\n"
                f"Our team will now review your submission."
            )

        await interaction.response.send_message(
            "✅ Thank you! Your additional info has been submitted and will be reviewed shortly.",
            ephemeral=True
        )

class RiskAgreementView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.select(
        placeholder="⚠️ Read the warning and confirm to proceed.",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="✅ I have read and accept the risks of false information.",
                value="agreed"
            )
        ]
    )
    async def confirm_warning(self, interaction: discord.Interaction, select: Select):
        if select.values[0] == "agreed":
            await interaction.response.send_modal(CreatorInfoModal(self.bot))

class AssignButton(discord.ui.Button):
    def __init__(self, campaign_id):
        super().__init__(label="Assign to creator", style=discord.ButtonStyle.primary)
        self.campaign_id = campaign_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"🛠 Assigning campaign {self.campaign_id}...", ephemeral=True)
        # Hier später richtige Logik einbauen


class CampaignActionView(View):
    def __init__(self, campaign_name):
        super().__init__(timeout=None)
        self.campaign_name = campaign_name

class CommentModal(Modal, title="Add Campaign Comment"):
    def __init__(self, campaign_name):
        super().__init__()
        self.campaign_name = campaign_name
        self.comment = TextInput(label="Your comment", placeholder="e.g. Video is scheduled for tomorrow!", required=True)
        self.add_item(self.comment)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"📝 Comment added to **{self.campaign_name}**:\n> {self.comment.value}",
            ephemeral=False
        )

class SubmitModal(Modal, title="Submit Campaign Result"):
    def __init__(self, campaign_name):
        super().__init__()
        self.campaign_name = campaign_name
        self.submission = TextInput(label="Link to your post / video", placeholder="Paste the link here", required=True)
        self.add_item(self.submission)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"📎 Submission for **{self.campaign_name}** received:\n> {self.submission.value}",
            ephemeral=False
        )

    @discord.ui.button(label="✏️ Add Comment", style=discord.ButtonStyle.blurple)
    async def comment(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(CommentModal(self.campaign_name))

    @discord.ui.button(label="📎 Submit", style=discord.ButtonStyle.green)
    async def submit(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SubmitModal(self.campaign_name))

@app.on_event("startup")
async def start_background_tasks():
    await bot.wait_until_ready()
    asyncio.create_task(auto_decline_expired())

@bot.tree.command(name="apply", description="Apply for Elysium access")
async def apply_command(interaction: discord.Interaction):
    guild = interaction.guild
    user = interaction.user

    code = "elysium-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    verification_codes[user.id] = f"#{code}"
    channel_name = f"verify-{code.lower()}"

    existing = discord.utils.get(guild.text_channels, name=channel_name)
    if existing:
        await interaction.response.send_message("You already have a verify channel.", ephemeral=True)
        return

    bot_role = discord.utils.get(guild.roles, name="Jake Bot")
    admin_role = discord.utils.get(guild.roles, name="Admin")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False,
            use_application_commands=True
        ),
        user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            use_application_commands=True
        ),
    }
    if bot_role:
        overwrites[bot_role] = discord.PermissionOverwrite(view_channel=True)
    if admin_role:
        overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)

    channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites, topic=code)
    await channel.send(
        f"Hi {user.mention}, welcome to Elysium!\n"
        f"Please place this code visibly in your profile:\n**#{code}**\n"
        f"Then run `/verify platform:<platform> username:<your_username>` here."
    )

    await interaction.response.send_message("✅ Your private verification channel has been created.", ephemeral=True)

SUBMISSIONS_PATH = os.path.join(BASE_DIR, "campaign-ui", "campaign-ui", "submissions.json")

@bot.tree.command(name="verify", description="Verify your social profile by code")
@app_commands.describe(
    platform="Platform (TikTok, Instagram, YouTube, Spotify)",
    username="Your username or playlist ID"
)
async def verify_command(interaction: discord.Interaction, platform: str, username: str):
    from tiktok_scraper import get_tiktok_bio
    from instagram_scraper import get_instagram_bio
    from youtube_scraper import get_youtube_description
    from spotify_scraper import get_playlist_description

    user = interaction.user
    user_id = user.id
    code = verification_codes.get(user.id)

    if not code:
        await interaction.response.send_message(
            "❌ Du hast keinen aktiven Verifizierungscode. Bitte zuerst `/apply` ausführen.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)
    platform = platform.lower()
    bio = None

    try:
        if platform == "tiktok":
            bio = await get_tiktok_bio(username, code)
        elif platform == "instagram":
            bio = await get_instagram_bio(username, code)
        elif platform == "youtube":
            bio = await get_youtube_description(username, code)
        elif platform == "spotify":
            bio = await get_playlist_description(username, code)
        else:
            await interaction.followup.send("❌ Unbekannte Plattform. Bitte wähle TikTok, Instagram, YouTube oder Spotify.")
            return
    except Exception as e:
        await interaction.followup.send(f"⚠️ Fehler beim Scraping des Profils: {e}")
        return

    if not bio or code.lower() not in bio.lower():
        await interaction.followup.send(
            f"❌ Dein Code `{code}` wurde auf dem Profil **nicht gefunden**.\n"
            f"Bitte stelle sicher, dass er sichtbar in deiner Bio oder Beschreibung steht.",
        )
        return

    # ✅ Code wurde gefunden → Speichere Temp Submission
    bot.temp_submissions[user.id] = {
        "platform": platform,
        "username": username,
        "bio": bio,
        "code": code
    }

    await interaction.followup.send(
        content=(
            "**⚠️ Final Warning – Read Carefully!**\n\n"
            "By continuing, you confirm that the information you’re about to provide is **truthful**.\n"
            "**Any attempt to manipulate views, follower stats, or pricing will result in a permanent ban** and full denial of payment.\n\n"
            "If you're unsure, please **cancel** now and contact support first."
        ),
        view=RiskAgreementView(bot)
    )
    
class SubmissionReviewView(View):
    def __init__(self, bot, submission):
        super().__init__(timeout=None)
        self.bot = bot
        self.submission = submission

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        guild = interaction.guild
        user = guild.get_member(self.submission["user_id"])

        if not user:
            await interaction.followup.send("User not found.")
            return

        trusted_role = discord.utils.get(guild.roles, name="Trusted")
        if trusted_role:
            try:
                await user.add_roles(trusted_role)
            except Exception as e:
                await interaction.followup.send(f"⚠️ Could not assign role: {e}", ephemeral=False)

        channel_name = f"t-creator-{user.name.lower()}-{self.submission['platform']}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True),
        }
        bot_role = discord.utils.get(guild.roles, name="Jake Bot")
        admin_role = discord.utils.get(guild.roles, name="Admin")
        if bot_role:
            overwrites[bot_role] = discord.PermissionOverwrite(view_channel=True)
        if admin_role:
            overwrites[admin_role] = discord.PermissionOverwrite(view_channel=True)

        creator_channel = None
        expected_prefix = f"t-creator-{user.name.lower()}-{self.submission['platform']}"
        for channel in interaction.guild.text_channels:
            if channel.name.startswith(expected_prefix):
                creator_channel = channel
                break

        embed = discord.Embed(
            title="Welcome to Elysium!",
            description=(
                f"{user.mention}, your submission has been accepted.\n\n"
                "You're now part of our Creator Network and eligible for campaigns.\n"
                "Stay tuned for updates and opportunities right here."
            ),
            color=discord.Color.green()
        )

        if not creator_channel:
            try:
                creator_channel = await guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    topic=self.submission["code"][1:],
                    reason="New trusted creator accepted"
                )
            except Exception as e:
                await interaction.followup.send(f"❌ Failed to create channel: {e}", ephemeral=True)
                return

        await creator_channel.send(
            f"🎉 Congratulations {user.mention}!\n\n"
            f"You've been officially accepted into the Elysium Creator Program.\n"
            f"You're now eligible to receive paid campaigns right here in this channel.\n\n"
            f"Stay active, follow the instructions carefully – and let’s grow together!"
        )

        # ✅ Jetzt Status speichern
        with open("submissions.json", "r") as f:
            subs = json.load(f)
        for s in subs:
            if s["user_id"] == self.submission["user_id"] and s["platform"] == self.submission["platform"]:
                s["status"] = "approved"
        with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
            json.dump(subs, f, indent=2)

        await interaction.followup.send(f"{user.mention} has been accepted.")

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        guild = interaction.guild
        user = guild.get_member(self.submission["user_id"])

        verify_channel = next(
            (c for c in guild.text_channels if c.topic == self.submission["code"][1:]),
            None
        )

        if user:
            try:
                await user.send("Your submission was declined. You are welcome to reapply anytime.")
            except:
                pass

        if verify_channel:
            await verify_channel.send(
                f"{user.mention}, thanks again for your submission.\n\n"
                "After reviewing your profile, we've decided not to proceed at this time.\n"
                "You’re welcome to apply again in the future with updates or new platforms."
            )

        with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
            subs = json.load(f)
        subs = [
            s for s in subs
            if not (
                s["user_id"] == self.submission["user_id"] and
                s["platform"] == self.submission["platform"]
            )
        ]
        with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
            json.dump(subs, f, indent=2)

        class DeleteView(View):
            @discord.ui.button(label="🗑️ Delete now", style=discord.ButtonStyle.grey)
            async def delete_channel(self, interaction2: discord.Interaction, button: Button):
                if verify_channel:
                    await verify_channel.delete()
                await interaction2.response.send_message("Channel deleted.", ephemeral=False)

        await interaction.followup.send(
            f"{user.mention} has been declined. You can delete the verify channel now or let it expire later.",
            view=DeleteView()
        )

    @discord.ui.button(label="🔁 More Info", style=discord.ButtonStyle.blurple)
    async def more_info(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        guild = interaction.guild
        user = guild.get_member(self.submission["user_id"])
        verify_channel = next((c for c in guild.text_channels if c.topic == self.submission["code"][1:]), None)

        if user:
            try:
                await user.send("We’d love to know more before we decide. Could you share more details or stats?")
            except:
                pass

        if verify_channel:
            await interaction.followup.send(f"Jump to verify channel: {verify_channel.mention}")
        else:
            await interaction.followup.send("Couldn't find the verify channel.")

@bot.tree.command(name="review-submissions", description="Review all pending applications")
async def review_submissions(interaction: discord.Interaction):
    if not discord.utils.get(interaction.user.roles, name="Admin"):
        await interaction.response.send_message("Only Admins can use this command.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    try:
        with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
            subs = json.load(f)
    except:
        subs = []

    pending = [s for s in subs if s["status"] == "pending"]

    if not pending:
        await interaction.followup.send("✅ No pending applications.")
        return

    for sub in pending:
        embed = discord.Embed(title=f"{sub['username']} – {sub['platform'].capitalize()} Submission")
        details = sub.get("details")
        if details:
            embed.add_field(
                name="📊 Stats & Prices",
                value=(
                    f"**Views (30d):** {details.get('views_last_30', 'N/A')}\n"
                    f"**New Followers (30d):** {details.get('new_followers', 'N/A')}\n"
                    f"**Price:** {details.get('price', 'N/A')}\n"
                    f"**Extras:** {details.get('extra_offers', '–')}"
                ),
                inline=False
            )


        handle = sub["handle"]
        platform = sub["platform"].lower()
        link = {
            "tiktok": f"https://www.tiktok.com/@{handle}",
            "instagram": f"https://www.instagram.com/{handle}",
            "youtube": f"https://www.youtube.com/@{handle}",
            "spotify": f"https://open.spotify.com/playlist/{handle}"
        }.get(platform, "Unknown")

        embed.add_field(name="Platform Link", value=link, inline=False)
        await interaction.followup.send(embed=embed, view=SubmissionReviewView(bot, sub))

@bot.tree.command(name="campaign-status", description="Zeigt den Status einer bestimmten Kampagne an.")
async def campaign_status(interaction: discord.Interaction, campaign_id: str):
    try:
        if not os.path.exists(CAMPAIGN_RESPONSES_FILE):
            await interaction.response.send_message("Es gibt noch keine gespeicherten Kampagnen.")
            return

        with open(CAMPAIGN_RESPONSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        campaign = next((c for c in data if c.get("campaign_id") == campaign_id), None)
        if not campaign:
            await interaction.response.send_message(f"Keine Kampagne mit ID **{campaign_id}** gefunden.")
            return

        accepted = [c["name"] for c in campaign.get("creators", []) if c.get("status") == "accepted"]
        declined = [c["name"] for c in campaign.get("creators", []) if c.get("status") == "declined"]
        pending = [c["name"] for c in campaign.get("creators", []) if c.get("status") == "pending"]

        msg = (
            f"**Status für Kampagne {campaign_id}:**\n"
            f"**Angenommen:** {', '.join(accepted) if accepted else 'Keine'}\n"
            f"**Abgelehnt:** {', '.join(declined) if declined else 'Keine'}\n"
            f"**Offen:** {', '.join(pending) if pending else 'Keine'}"
        )

        await interaction.response.send_message(msg)

    except Exception as e:
        await interaction.response.send_message(f"Fehler beim Abrufen des Status: {e}")


@bot.tree.command(name="status", description="Zeigt den Status aller Kampagnen an.")
async def status(interaction: discord.Interaction):
    try:
        if not os.path.exists(CAMPAIGN_RESPONSES_FILE):
            await interaction.response.send_message("Es gibt noch keine gespeicherten Kampagnen.")
            return

        with open(CAMPAIGN_RESPONSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not data:
            await interaction.response.send_message("Es sind keine Kampagnen vorhanden.")
            return

        msg = "**Status aller Kampagnen:**\n"
        for c in data:
            cid = c.get("campaign_id", "Unbekannt")
            accepted = sum(1 for x in c.get("creators", []) if x.get("status") == "accepted")
            total = len(c.get("creators", []))
            msg += f"- {cid}: {accepted}/{total} akzeptiert\n"

        await interaction.response.send_message(msg)

    except Exception as e:
        await interaction.response.send_message(f"Fehler beim Abrufen der Kampagnenübersicht: {e}")

@bot.tree.command(name="review-campaigns", description="Review and assign campaigns to creators")
async def review_campaigns(interaction: discord.Interaction):
    if not discord.utils.get(interaction.user.roles, name="Admin"):
        await interaction.response.send_message("Only Admins can review campaigns.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=False)

    try:
        with open("campaigns.json", "r") as f:
            campaigns = json.load(f)
    except:
        campaigns = []

    if not campaigns:
        await interaction.followup.send("📭 No campaigns found.")
        return
        
    for campaign in campaigns:
        campaign_id = campaign["id"]
        embed = discord.Embed(title=f"📢 {campaign['title']}", description=campaign["description"], color=discord.Color.teal())
        embed.add_field(name="💰 Reward", value=campaign["reward"], inline=True)
        embed.add_field(name="📅 Deadline", value=campaign["deadline"], inline=True)
        embed.add_field(name="🔖 Status", value=campaign["status"], inline=True)
        embed.add_field(name="🆔 Campaign ID", value=campaign_id, inline=False)

        view = View()
        view.add_item(AssignButton(str(campaign_id)))  # cast zu str falls nötig


        await interaction.followup.send(embed=embed, view=view)

@bot.tree.command(name="assign-campaign", description="Assign a campaign to a creator")
@app_commands.describe(
    campaign_id="The ID of the campaign",
    creator_id="The Discord User ID of the creator"
)
async def assign_campaign(interaction: discord.Interaction, campaign_id: str, creator_id: str):

    if not discord.utils.get(interaction.user.roles, name="Admin"):
        await interaction.response.send_message("Only Admins can assign campaigns.", ephemeral=True)
        return

    try:
        with open("campaigns.json", "r") as f:
            campaigns = json.load(f)
    except:
        await interaction.response.send_message("Error loading campaigns.json", ephemeral=True)
        return

    campaign = next((c for c in campaigns if str(c["id"]) == campaign_id), None)
    if not campaign:
        await interaction.response.send_message("❌ Campaign not found.", ephemeral=True)
        return

    guild = interaction.guild
    user = interaction.guild.get_member(int(creator_id))

    if not user:
        await interaction.response.send_message("❌ Creator not found in server.", ephemeral=True)
        return

    # Finde den Creator-Channel
    channel_name_part = f"t-creator-{user.name.lower()}"
    target_channel = next((c for c in guild.text_channels if c.name.startswith(channel_name_part)), None)

    if not target_channel:
        await interaction.response.send_message("❌ Couldn’t find the creator’s channel.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"📢 New Campaign: {campaign['title']}",
        description=campaign["description"],
        color=discord.Color.gold()
    )
    embed.add_field(name="💰 Reward", value=campaign["reward"], inline=True)
    embed.add_field(name="📅 Deadline", value=campaign["deadline"], inline=True)
    embed.set_footer(text=f"Campaign ID: {campaign['id']}")

    await target_channel.send(
        f"{user.mention}, here's a new campaign opportunity for you 👇",
        embed=embed,
        view=CampaignActionView(campaign["title"])
    )

    # Finde den Creator-Channel

@bot.tree.command(name="my-campaigns", description="Show your active campaigns")
async def my_campaigns(interaction: discord.Interaction):
    user = interaction.user
    guild = interaction.guild

    try:
        with open("campaigns.json", "r") as f:
            campaigns = json.load(f)
    except:
        await interaction.response.send_message("Could not load campaign list.", ephemeral=True)
        return

    # Filter: Welche Campaigns wurden diesem User bereits gesendet?
    # (Wir verwenden den Creator-Channel als Nachweis)

    relevant_channels = [
    c for c in guild.text_channels
    if c.topic and str(user.id) in c.topic
    ]

    if not relevant_channels:
        await interaction.response.send_message("You don’t have a creator channel yet.", ephemeral=True)
        return

    found = []
    async for message in relevant_channels[0].history(limit=100):
        if message.embeds:
            embed = message.embeds[0]
            if embed.title and embed.title.startswith("📢 New Campaign"):
                found.append(embed)

    if not found:
        await interaction.response.send_message("You don’t have any campaigns yet.", ephemeral=True)
        return

    for embed in found:
        await interaction.user.send(embed=embed)

    await interaction.response.send_message("📩 Sent your active campaigns to your DMs.", ephemeral=True)

# -------------- Campaign Creator UI -----------------
class CreatorFilterDropdown(Select):
    def __init__(self, creators):
        options = [
            discord.SelectOption(label=c["username"], value=str(c["user_id"]))
            for c in creators
        ]
        super().__init__(
            placeholder="Select creators (multiple allowed)",
            options=options,
            min_values=1,
            max_values=len(options)
        )

class CampaignCreatorView(View):
    def __init__(self, bot):
        super().__init__(timeout=600)   # 10 min
        self.bot = bot

        # --- Daten laden: alle approved Creator -----------
        try:
            with open("campaign-ui/campaign-ui/submissions.json", "r") as f:
                subs = json.load(f)
        except:
            subs = []

        self.approved = [s for s in subs if s.get("status") == "approved"]

        if not self.approved:
            # Fallback-Button, falls noch niemand approved ist
            self.add_item(
                Button(
                    label="No approved creators yet",
                    style=discord.ButtonStyle.grey,
                    disabled=True
                )
            )
            return

        # --- Dropdown hinzufügen --------------------------
        self.dropdown = CreatorFilterDropdown(self.approved)
        self.add_item(self.dropdown)

        # --- Bestätigungs-Button --------------------------
        self.add_item(CampaignConfirmButton())

class CampaignConfirmButton(Button):
    def __init__(self):
        super().__init__(label="✅ Create & assign", style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        view: CampaignCreatorView = self.view          # Typ casting
        selected_ids = view.dropdown.values            # Liste der gewählten User-IDs (str)
        if not selected_ids:
            await interaction.response.send_message(
                "⚠️ Please select at least one creator.", ephemeral=True
            )
            return

        # -------- Kampagne in campaigns.json speichern ----
        try:
            with open("campaigns.json", "r") as f:
                campaigns = json.load(f)
        except:
            campaigns = []

        new_id = len(campaigns) + 1
        campaigns.append({
            "id": new_id,
            "title": "Untitled",           # Platzhalter – kannst Du später per Modal abfragen
            "description": "–",
            "reward": "–",
            "deadline": "–",
            "status": "active",
            "assigned": selected_ids
        })
        with open("campaigns.json", "w") as f:
            json.dump(campaigns, f, indent=2)

        # -------- Creator-Channel anpingen ----------------
        guild = interaction.guild
        for uid in selected_ids:
            member = guild.get_member(int(uid))
            if not member:
                continue
            channel_name_part = f"t-creator-{member.name.lower()}"
            creator_ch = next(
                (c for c in guild.text_channels if c.name.startswith(channel_name_part)),
                None
            )
            if creator_ch:
                await creator_ch.send(
                    f"{member.mention} – You’ve been assigned to a new campaign (ID {new_id}). "
                    "Please wait for further details!"
                )

        await interaction.response.send_message(
            f"✅ Campaign **#{new_id}** created and assigned to {len(selected_ids)} creator(s).",
            ephemeral=True
        )

class CampaignView(discord.ui.View):
    def __init__(self, campaign_id, creator_name):
        super().__init__(timeout=None)
        self.campaign_id = campaign_id
        self.creator_name = creator_name

    @discord.ui.button(label="✅ Ja", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await update_creator_status(self.campaign_id, self.creator_name, "accepted")
        await interaction.response.send_message(f"{self.creator_name} hat zugesagt!", ephemeral=True)

    @discord.ui.button(label="❌ Nein", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        await update_creator_status(self.campaign_id, self.creator_name, "declined")
        await interaction.response.send_message(f"{self.creator_name} hat abgelehnt.", ephemeral=True)

@bot.tree.command(name="finalize-campaign", description="Speichert die aktuelle Creator-Auswahl als neue Kampagne.")
@app_commands.checks.has_permissions(administrator=True)
async def finalize_campaign(interaction: discord.Interaction):
    # Zugriff auf die letzte verwendete View (wenn sie noch lebt)
    view: Optional[CreatorGridView] = bot.current_creator_view if hasattr(bot, "current_creator_view") else None

    if not view or not view.selected_creators:
        await interaction.response.send_message("⚠️ Keine Creator ausgewählt oder View nicht mehr aktiv.", ephemeral=True)
        return

    # Neue Kampagne erstellen
    campaign_data = {
        "created_at": datetime.datetime.utcnow().isoformat(),
        "creators": list(view.selected_creators)
    }

    # Bestehende Campaigns laden oder leeres Objekt
    if os.path.exists("campaigns.json"):
        with open("campaigns.json", "r") as f:
            campaigns = json.load(f)
    else:
        campaigns = {}

    campaign_id = str(uuid.uuid4())[:8]
    campaigns[campaign_id] = campaign_data

    # Speichern
    with open("campaigns.json", "w") as f:
        json.dump(campaigns, f, indent=2)

    await interaction.response.send_message(
        f"✅ Campaign `{campaign_id}` gespeichert mit {len(view.selected_creators)} Creator(s).",
        ephemeral=True
    )

def save_campaign_responses(campaign_id, creators):
    if not os.path.exists(CAMPAIGN_RESPONSES_FILE):
        data = []
    else:
        with open(CAMPAIGN_RESPONSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    data.append({
        "campaign_id": campaign_id,
        "creators": creators
    })

    with open(CAMPAIGN_RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

from datetime import datetime, timedelta

@app.post("/start-campaign")
async def start_campaign(request: Request):
    data = await request.json()
    creators = data if isinstance(data, list) else data.get("creators", [])
    message = data.get("message", "Willst du bei dieser Kampagne mitmachen?")

    campaign_id = generate_campaign_id()

    # Füge Deadline hinzu (z.B. 3 Tage)
    for creator in creators:
        creator["status"] = "pending"
        creator["deadline"] = (datetime.utcnow() + timedelta(days=3)).isoformat()

    save_campaign_responses(campaign_id, creators)

    print(f"Kampagne {campaign_id} gestartet mit: {creators}")

    # Auto-Channel für diese Kampagne erstellen
    guild = bot.guilds[0]
    discussion_channel_name = f"campaign-{campaign_id.lower()}-discussion"
    existing_channel = discord.utils.get(guild.text_channels, name=discussion_channel_name)
    if not existing_channel:
        await guild.create_text_channel(discussion_channel_name)

    # Nachricht ins campaign-updates Channel posten
    await send_campaign_update(f"🚀 Kampagne **{campaign_id}** gestartet mit {len(creators)} Creators.")

    # Nachrichten an alle Creator schicken
    for creator in creators:
        try:
            await send_campaign_message(campaign_id, creator, message)
        except Exception as e:
            print(f"❌ Fehler beim Senden an {creator.get('name')}: {e}")

    return {"status": "ok", "campaign_id": campaign_id}

@app.get("/api/campaign-status")
async def get_campaign_status():
    try:
        with open("campaign_responses.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"campaigns": data}
    except Exception as e:
        return {"error": str(e)}

async def send_campaign_message(campaign_id, creator, message):
    try:
        channel_name = f"t-creator-{creator['id']}"
        channel = discord.utils.get(bot.get_all_channels(), name=channel_name)

        if channel:
            view = CampaignView(campaign_id, creator["name"])
            await channel.send(
                f"👋 Hey {creator['name']},\n\n{message}\n\n**Platform:** {creator['platform']}",
                view=view
            )
            print(f"✅ Nachricht an {creator['name']} gesendet.")
        else:
            print(f"❌ Kein Channel gefunden für {creator['name']} ({channel_name})")
    except Exception as e:
        print(f"Fehler beim Senden an {creator['name']}: {e}")

import asyncio

import os
from fastapi.staticfiles import StaticFiles

from fastapi.staticfiles import StaticFiles
import os

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "campaign-ui",
    "campaign-ui"
)

app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

PUBLIC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "campaign-ui",
    "campaign-ui",
    "public"
)

# Nur EIN Mount, das Root + alle Files bereitstellt
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")
app.mount("/public", StaticFiles(directory="campaign-ui/campaign-ui/public"), name="public")

from datetime import datetime, timedelta
import asyncio

CHECK_INTERVAL = 10 # alle 6 Stunden

async def auto_decline_expired():
    while True:
        print("[DEBUG] Checking for expired campaigns...")  # Nur diese lassen!
        if not os.path.exists(CAMPAIGN_RESPONSES_FILE):
            await asyncio.sleep(30)
            continue

        with open(CAMPAIGN_RESPONSES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.utcnow()
        changed = False

        for campaign in data:
            for creator in campaign["creators"]:
                # Entferne hier ALLE extra Debug-Ausgaben (Prüfe Kampagne etc.)
                deadline = creator.get("deadline")
                if deadline and creator["status"] == "pending":
                    if datetime.fromisoformat(deadline) < now:
                        creator["status"] = "declined"
                        await send_campaign_update(
                            f"❌ Creator **{creator['name']}** hat nicht geantwortet (Auto-Decline)."
                        )
                        changed = True

        if changed:
            with open(CAMPAIGN_RESPONSES_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        await asyncio.sleep(30)

@app.get("/debug-files")
def debug_files():
    if not os.path.exists(PUBLIC_DIR):
        return {"error": "Directory not found", "dir": PUBLIC_DIR}
    return {"base_dir": PUBLIC_DIR, "files": os.listdir(PUBLIC_DIR)}

@tasks.loop(seconds=10)  # für produktiv: auf 3600 (1 Stunde) setzen
async def check_for_expired_responses():
    now = datetime.now().timestamp()
    printed_checking_message = False
    updated = False

    print("[Auto-Decline] Checking for expired responses...")

    campaign_responses = load_campaign_responses()
    for campaign_id, creators in campaign_responses.items():
        for creator_id, response in creators.items():
            if response["status"] == "pending":
                created_time = response["created"]
                if now - created_time >= 259200:  # 3 Tage in Sekunden
                    # Markiere als declined
                    response["status"] = "declined"
                    response["declined_by_system"] = True
                    updated = True

                    # Schicke automatische Nachricht
                    try:
                        user = await bot.fetch_user(int(creator_id))
                        await user.send(
                            f"⏰ Du hast nicht rechtzeitig auf die Kampagne **{campaign_id}** geantwortet.\n"
                            f"Du wurdest automatisch abgelehnt. Bitte antworte beim nächsten Mal schneller, wenn du Interesse hast!"
                        )
                    except Exception as e:
                        print(f"[Auto-Decline] Fehler beim Senden an {creator_id}: {e}")

    if updated:
        with open("campaign_responses.json", "w") as f:
            json.dump(campaign_responses, f, indent=4)
        print("[Auto-Decline] Updates gespeichert.")

@tasks.loop(seconds=10)  # für produktiv: auf 3600 (1 Stunde) setzen
async def auto_decline_expired():
    print("[Auto-Decline] Checking for expired campaigns...")
    data = load_json("campaign-ui/campaign-ui/submissions.json")

    if isinstance(data, list):
        for entry in data:
            creator_id = entry.get("creator_id")
            campaigns = entry.get("campaigns", [])
            updated_campaigns = []

            for campaign in campaigns:
                created_at_str = campaign.get("created_at")
                if created_at_str:
                    created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
                    if datetime.now() - created_at > timedelta(hours=24):
                        campaign["status"] = "auto-declined"
                        campaign["decline_reason"] = "Zeitlimit überschritten"
                    else:
                        updated_campaigns.append(campaign)

            entry["campaigns"] = updated_campaigns
    else:
        print("[Auto-Decline] Unexpected data format in submissions.json – expected list.")
        return

    save_json("submissions.json", data)

# Start loop beim Bot-Start
@bot.event
async def on_ready():
    if not auto_decline_expired.is_running():
        auto_decline_expired.start()
    print(f"✅ Bot is ready: {bot.user}")

# Starte Task beim Bot-Start
@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    check_for_expired_responses.start()

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"[Slash Commands] {len(synced)} Command(s) synchronisiert.")
    except Exception as e:
        print(f"[Slash Commands] Fehler bei sync: {e}")

# Starte Bot in Hintergrund-Task
async def start_bot():
    await bot.start(TOKEN)

loop = asyncio.get_event_loop()
loop.create_task(start_bot())  # Bot läuft im Hintergrund

bot.run(TOKEN)
