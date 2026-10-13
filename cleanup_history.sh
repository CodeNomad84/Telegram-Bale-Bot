#!/usr/bin/env bash
# =============================================================================
# cleanup_history.sh — حذف فایل‌های حساس از «کل» تاریخچهٔ git
#
# اجرا (در Git Bash یا لینوکس، داخل مخزن):   bash cleanup_history.sh
# راهنمای کامل و پیش‌نیازها:                 SECURITY_CLEANUP.md
#
# مراحل:
#   ۰) بررسی پیش‌نیازها (filter-repo، working tree تمیز، branchها، وضعیت remote)
#   ۱) نمایش فایل‌هایی که پاک می‌شوند                        ← تأیید ۱
#   ۲) پشتیبان کامل (git bundle + کپی .env و keramat.db)
#   ۳) بازنویسی تاریخچه با git filter-repo (همهٔ branchهای محلی با هم)
#   ۴) بررسی نتیجه (هیچ فایل حساسی در تاریخچه نمانده باشد)
#   ۵) force-push شاخهٔ main به GitHub                       ← تأیید ۲
#
# branch اصلاحات (fix/claude-review-fixes) push «نمی‌شود»؛ آن را خودتان push کنید.
# =============================================================================
set -euo pipefail
# Git Bash ویندوز آرگومان‌هایی مثل "branch:path" را مسیر فرض می‌کند و تغییرشان می‌دهد
export MSYS_NO_PATHCONV=1

REMOTE_NAME="origin"
REMOTE_URL="${REMOTE_URL:-https://github.com/CodeNomad84/Telegram-Bale-Bot.git}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"
FIX_BRANCH="${FIX_BRANCH:-fix/claude-review-fixes}"

# الگوهایی که از کل تاریخچه حذف می‌شوند (glob در filter-repo از «/» هم عبور می‌کند)
FILTER_ARGS=(
  --invert-paths
  --path .env                          # توکن ربات و شناسه ادمین‌ها
  --path-glob '*.db'                   # keramat.db (شماره تلفن کاربران)
  --path-glob '*.sqlite3'
  --path-glob '*.pem'                  # کلید خصوصی سرور
  --path-glob '*.ppk'
  --path-glob '*export_users_*.xlsx'   # خروجی کاربران (شماره تلفن)
  --path-glob '*graph_*.png'           # نمودار دعوت (شناسه کاربران)
)
# همان الگوها به‌صورت regex برای بررسی قبل و بعد (.env.local.example را نمی‌گیرد)
SENSITIVE_REGEX='(^|/)\.env$|\.db$|\.sqlite3$|\.pem$|\.ppk$|(^|/)export_users_[^/]*\.xlsx$|(^|/)graph_[^/]*\.png$'

# فایل‌های محلی (ignored) که باید بعد از اجرا سر جایشان باشند
LOCAL_SECRETS=(.env Quizbot/database/keramat.db)

say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m[✓] %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m[!] %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m[✗] %s\033[0m\n' "$*" >&2; exit 1; }
confirm() {
  local reply
  read -r -p "$1 (yes/no): " reply
  [[ "$reply" == "yes" ]]
}
sensitive_paths() {
  git log --all --format= --name-only | sort -u | grep -E "$SENSITIVE_REGEX" || true
}

# ----------------------------------------------------------------------------
say "۰) بررسی پیش‌نیازها"
# ----------------------------------------------------------------------------
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || die "این اسکریپت باید داخل مخزن git اجرا شود."

if git filter-repo --version >/dev/null 2>&1; then
  FILTER_REPO=(git filter-repo)
elif python -m git_filter_repo --version >/dev/null 2>&1; then
  FILTER_REPO=(python -m git_filter_repo)
elif python3 -m git_filter_repo --version >/dev/null 2>&1; then
  FILTER_REPO=(python3 -m git_filter_repo)
else
  die "git-filter-repo نصب نیست. نصب: pip install git-filter-repo"
fi
ok "git-filter-repo: $("${FILTER_REPO[@]}" --version)"

# روی main، فایل .gitignore هنوز UTF-16 و بی‌اثر است و .env «untracked» دیده می‌شود
[[ "$(git symbolic-ref --short -q HEAD || true)" == "$FIX_BRANCH" ]] \
  || die "اول به branch اصلاحات بروید: git checkout $FIX_BRANCH"
[[ -z "$(git status --porcelain)" ]] || die "working tree تمیز نیست. اول تغییرات را commit یا stash کنید (git status)."
[[ -z "$(git stash list)" ]] || die "stash دارید. stashها با تاریخچهٔ قدیم می‌مانند؛ اول آن‌ها را اعمال یا حذف کنید (git stash list)."
git rev-parse --verify -q "refs/heads/$MAIN_BRANCH" >/dev/null || die "branch '$MAIN_BRANCH' وجود ندارد."
git rev-parse --verify -q "refs/heads/$FIX_BRANCH" >/dev/null || die "branch '$FIX_BRANCH' وجود ندارد."
ok "working tree تمیز است و branchها موجودند."

CURRENT_URL="$(git remote get-url "$REMOTE_NAME" 2>/dev/null || true)"
[[ "$CURRENT_URL" == "$REMOTE_URL" ]] || die "آدرس remote '$REMOTE_NAME' با '$REMOTE_URL' یکی نیست (فعلی: '${CURRENT_URL:-ندارد}')."

OLD_REMOTE_MAIN="$(git ls-remote "$REMOTE_NAME" "refs/heads/$MAIN_BRANCH" | cut -f1)"
[[ -n "$OLD_REMOTE_MAIN" ]] || die "شاخهٔ $MAIN_BRANCH روی remote پیدا نشد (اتصال اینترنت/دسترسی را بررسی کنید)."
git cat-file -e "${OLD_REMOTE_MAIN}^{commit}" 2>/dev/null \
  || die "روی remote کامیتی هست که محلی ندارید. اول git fetch و ادغام کنید، بعد دوباره اجرا کنید."
git merge-base --is-ancestor "$OLD_REMOTE_MAIN" "$MAIN_BRANCH" \
  || die "شاخهٔ $MAIN_BRANCH محلی از remote عقب است یا جدا شده. اول همگام کنید."
ok "remote $MAIN_BRANCH = ${OLD_REMOTE_MAIN:0:7} (در $MAIN_BRANCH محلی موجود است)"

OTHER_REMOTE_BRANCHES="$(git ls-remote --heads "$REMOTE_NAME" | cut -f2 | grep -v "^refs/heads/$MAIN_BRANCH$" || true)"
if [[ -n "$OTHER_REMOTE_BRANCHES" ]]; then
  warn "این branchهای remote push نمی‌شوند و تاریخچهٔ قدیم را نگه می‌دارند (بعداً حذف یا بازنویسی کنید):"
  sed 's/^/      /' <<< "$OTHER_REMOTE_BRANCHES"
fi

# ----------------------------------------------------------------------------
say "۱) فایل‌هایی که از کل تاریخچه حذف می‌شوند"
# ----------------------------------------------------------------------------
BEFORE="$(sensitive_paths)"
if [[ -z "$BEFORE" ]]; then
  ok "هیچ فایل حساسی در تاریخچه نیست؛ کاری لازم نیست."
  exit 0
fi
sed 's/^/      /' <<< "$BEFORE"
echo
echo "    این کار hash «همهٔ» کامیت‌ها را در همهٔ branchهای محلی عوض می‌کند"
echo "    ($MAIN_BRANCH و $FIX_BRANCH با هم بازنویسی می‌شوند؛ rebase لازم نیست)."
confirm "ادامه و ساخت پشتیبان؟" || die "لغو شد. هیچ تغییری انجام نشد."

# ----------------------------------------------------------------------------
say "۲) پشتیبان‌گیری"
# ----------------------------------------------------------------------------
TS="$(date +%Y%m%d_%H%M%S)"
# مسیر از git گرفته می‌شود (روی ویندوز F:/...) تا هم bash و هم git.exe آن را بفهمند
BACKUP_DIR="$(dirname "$(git rev-parse --show-toplevel)")/history-backup-$TS"
mkdir -p "$BACKUP_DIR"
git bundle create "$BACKUP_DIR/repo-before-cleanup.bundle" --all
git bundle verify "$BACKUP_DIR/repo-before-cleanup.bundle" >/dev/null
git for-each-ref --format='%(objectname) %(refname)' > "$BACKUP_DIR/refs-before-cleanup.txt"
for f in "${LOCAL_SECRETS[@]}"; do
  if [[ -f "$f" ]]; then cp -p "$f" "$BACKUP_DIR/$(basename "$f")"; fi
done
ok "پشتیبان: $BACKUP_DIR"
warn "این پوشه حاوی توکن و دیتابیس است؛ بعد از اطمینان از موفقیت، امن پاکش کنید و هرگز آپلودش نکنید."

# ----------------------------------------------------------------------------
say "۳) بازنویسی تاریخچه با git filter-repo"
# ----------------------------------------------------------------------------
# --force: چون این یک clone تازه نیست (روی مخزن کاری اجرا می‌شود تا branch محلی
# اصلاحات هم بازنویسی شود). filter-repo در پایان remote «origin» را حذف می‌کند.
"${FILTER_REPO[@]}" --force "${FILTER_ARGS[@]}"

# ----------------------------------------------------------------------------
say "۴) بررسی نتیجه"
# ----------------------------------------------------------------------------
LEFT="$(sensitive_paths)"
[[ -z "$LEFT" ]] || die "هنوز در تاریخچه مانده: $LEFT — از $BACKUP_DIR/repo-before-cleanup.bundle بازیابی کنید."
[[ -z "$(git log --all --full-history --format=%h -- .env)" ]] || die "git log --all --full-history -- .env هنوز نتیجه دارد."
ok "هیچ فایل حساسی در تاریخچه نمانده (git log --all --full-history -- .env خالی است)."

git merge-base --is-ancestor "$MAIN_BRANCH" "$FIX_BRANCH" \
  || die "$FIX_BRANCH دیگر از $MAIN_BRANCH منشعب نیست؛ غیرمنتظره است. از پشتیبان بازیابی کنید."
ok "$FIX_BRANCH همچنان روی $MAIN_BRANCH جدید قرار دارد (rebase لازم نیست)."

git cat-file -e "$FIX_BRANCH:.env.local.example" 2>/dev/null \
  || die ".env.local.example از $FIX_BRANCH حذف شده؛ نباید این‌طور باشد."
ok ".env.local.example سالم است."

for f in "${LOCAL_SECRETS[@]}"; do
  if [[ -f "$f" ]]; then ok "فایل محلی $f سر جایش است."
  else warn "فایل محلی $f نیست؛ از $BACKUP_DIR کپی کنید."; fi
done

git remote get-url "$REMOTE_NAME" >/dev/null 2>&1 || git remote add "$REMOTE_NAME" "$REMOTE_URL"
ok "remote '$REMOTE_NAME' دوباره تنظیم شد (هنوز چیزی push نشده)."

# ----------------------------------------------------------------------------
say "۵) force-push شاخهٔ $MAIN_BRANCH"
# ----------------------------------------------------------------------------
echo "    $MAIN_BRANCH جدید:"
git log --oneline -5 "$MAIN_BRANCH" | sed 's/^/      /'
echo
echo "    با push، تاریخچهٔ $MAIN_BRANCH روی GitHub جایگزین می‌شود."
echo "    --force-with-lease فقط وقتی push می‌کند که remote هنوز روی ${OLD_REMOTE_MAIN:0:7} باشد."
if ! confirm "force-push $MAIN_BRANCH به $REMOTE_NAME؟"; then
  warn "push انجام نشد. هر وقت آماده بودید:"
  echo "      git push --force-with-lease=$MAIN_BRANCH:$OLD_REMOTE_MAIN $REMOTE_NAME $MAIN_BRANCH"
  echo "      git fetch $REMOTE_NAME && git branch --set-upstream-to=$REMOTE_NAME/$MAIN_BRANCH $MAIN_BRANCH"
  exit 0
fi

git push --force-with-lease="$MAIN_BRANCH:$OLD_REMOTE_MAIN" "$REMOTE_NAME" "$MAIN_BRANCH"
if [[ -n "$(git tag)" ]]; then
  git push --force --tags "$REMOTE_NAME"
fi
git fetch "$REMOTE_NAME"
git branch --set-upstream-to="$REMOTE_NAME/$MAIN_BRANCH" "$MAIN_BRANCH" >/dev/null
[[ -z "$(git log --all --full-history --format=%h -- .env)" ]] \
  || warn "بعد از fetch، .env دوباره در تاریخچه دیده می‌شود؛ احتمالاً branch دیگری روی remote تاریخچهٔ قدیم را دارد."
ok "$MAIN_BRANCH روی GitHub بازنویسی شد."

say "قدم‌های بعدی (دستی)"
cat <<EOF
  1. توکن ربات را از BotFather عوض کنید (اگر هنوز نکرده‌اید).
  2. روی سرور (هرگز git pull نزنید؛ تاریخچهٔ قدیم را برمی‌گرداند):
       cd /home/ubuntu/Telegram-Bale-Bot && git fetch origin && git reset --hard origin/$MAIN_BRANCH
  3. branch اصلاحات را بعد از بررسی خودتان push کنید:
       git push -u $REMOTE_NAME $FIX_BRANCH
  4. هر clone دیگر (سیستم دیگر) را دوباره clone کنید.
  5. برای حذف کامیت‌های قدیمی از کش GitHub به GitHub Support درخواست بدهید.
  6. بعد از اطمینان، پوشهٔ پشتیبان را پاک کنید: $BACKUP_DIR
EOF
