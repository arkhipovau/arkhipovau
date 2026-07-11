# Julie Arkhipova — Portfolio (локальная версия)

> **Статус: WIP (Work In Progress)**  
> Это не финальный продакшен-сайт, а активная пересборка портфолио с [arkhipovau.xyz](https://arkhipovau.xyz). Часть страниц, контента и визуальных решений ещё в работе. Не деплоить как финальную версию без явного решения.

Последнее обновление мануала: июль 2026.

> **Честный ответ:** мануал описывает рабочий процесс и архитектуру, но не заменяет чтение кода. Ниже — всё, что зафиксировано на сегодня; если что-то меняется в репозитории, обновляй этот файл.

---

## Что это за проект

Статический сайт-портфолио Julie Arkhipova. Без фреймворков и сборщиков — чистый HTML, CSS и немного JavaScript.

Дизайн собран из нескольких референсов:

| Источник | Что взято |
|----------|-----------|
| **Maison Margiela** | Типографика (Suisse Intl + Georgia), угловая навигация, сдержанная анимация |
| **Vanderbrand** | Таблица проектов на странице Index, сортировка |
| **Apple (MacBook Neo viewer)** | Playground — полноэкранный просмотр экспериментов |
| **Superpower** | Research — карусель эссе |

Оригинальный контент кейсов подтягивается с Readymag (arkhipovau.xyz) и хранится локально.

---

## Быстрый старт

### Запуск локально

Из корня репозитория:

```bash
cd /Users/arkhipovau/arkhipovau
python3 -m http.server 8080
```

Открыть в браузере: **http://localhost:8080**

Жёсткая перезагрузка при правках CSS/JS: **Cmd+Shift+R** (иначе браузер может показать кэш).

### Остановка сервера

В терминале, где запущен `http.server`: **Ctrl+C**.

---

## Карта сайта

| URL | Файл | Описание |
|-----|------|----------|
| `/` | `index.html` | Главная — сетка работ, фильтр Branding / Product / Research |
| `/index/` | `index/index.html` | Таблица всех проектов (Vanderbrand), сортировка по названию / типу / году |
| `/about/` | `about/index.html` | О себе, образование, услуги, контакты |
| `/cv/` | `cv/index.html` | Полное CV (двухколоночная вёрстка) |
| `/research/` | `research/index.html` | Карусель research-эссе |
| `/playground/` | `playground/index.html` | Лаборатория — 13 экспериментов, MacBook-style viewer |
| `/{slug}/` | `{slug}/index.html` | Страницы кейсов (см. список ниже) |

### Локальные страницы проектов (готовы)

- `run-ops`, `moretime`, `tokensfarm`, `burger-records`, `geoprotech`
- `white-secret-mouthfresher`, `artdom`, `magic-mirror`, `biomed`
- `illustrations-pack`, `splat-smilex`, `splat-special`
- `perception-of-beauty-in-the-installations-of-olafur-eliasson`
- `the-eyes-of-the-middle-ages-expressing-spiritual-dynamics-in-sculpture`

### Проекты на главной без локальной страницы

На главной (`index.html`) часть карточек помечена **Soon** — у них нет `uri` и локального `{slug}/index.html`:

Chichilaki, Crim, Veter Magazine, Blanc, Rhythmic, Steford Accelerator, Fields&Boxes и др.

На странице Index (`index/index.html`) аналогично: проекты с пустым `uri` не кликабельны.

### Есть локально, но нет на главной

Страницы `biomed/`, `splat-smilex/`, `splat-special/` собраны скриптом и живут на оригинале Readymag, но **не добавлены** в массив `projects` на главной и в Index-таблицу. Открываются только по прямому URL.

---

## Главная (`index.html`) — как устроена

Помимо угловой навигации, на главной есть отдельные механики:

### Tabnav-фильтр (центр экрана)

Плавающая pill-навигация (стиль Apple tabnav): **All · Branding · Product · Research**.

- Фильтрует карточки по полю `discipline` в массиве `projects`
- При выборе зоны — плавный scroll к секции
- Индикатор (полоска под активной вкладкой) пересчитывается при resize и загрузке шрифтов

`<body data-page="work">` — в NE-меню активен пункт **Work**.

### Три зоны контента

| `id` секции | Фильтр | Смысл |
|-------------|--------|-------|
| `branding` | Branding | Identity / packaging / logotype |
| `product` | Product | Sites / product / UX |
| `research` | Research | Essays / illustration / experiments |

Карточки рендерятся JS-ом при загрузке (`initPortfolio()`), не статичным HTML.

### Модель карточки (`projects[]`)

```js
{
  zone: 'identity',      // legacy, почти не используется в фильтре
  discipline: 'branding', // branding | product | research — для фильтра
  title: 'RUN–OPS',
  tags: 'Brand Identity',
  line: 'Короткий подзаголовок',  // опционально
  uri: 'run-ops',        // если нет — карточка «Soon», не кликабельна
  eco: true,             // опционально — уходит в блок Ecosystem
}
```

### Ecosystem

Проекты с `eco: true` (Fields&Boxes, research-эссе, Playground) показываются **отдельным блоком** под сеткой в своей зоне — компактный список с квадратными превью.

### Bio panel

Только в зоне **branding** — короткий bio-текст + кнопка **About**, открывающая оверлей.

### Оверлеи (только главная)

| ID | Назначение |
|----|------------|
| `overlay-about` | Краткий bio, Copy email, ссылка на `/about/`, кнопка Stay in touch |
| `overlay-contact` | Форма email — **без бэкенда**, по Submit открывает `mailto:` с введённым адресом |

Управление: `data-open`, `data-close`, Escape, клик по фону. API: `window.siteUI.openOverlay('overlay-about')`.

### Превью карточек

При загрузке fetch:

- `assets/images/manifest.json` — картинки кейсов
- `assets/images/card-heroes.json` — hero для карточек (по `uri` или `title`)

Логика `thumbFor()`: `p.img` → `card-heroes[uri|title]` → `manifest[uri].images[0]`.

Hero для проектов без кейса лежат в `assets/images/main/` (качаются скриптом download вместе с homepage).

### Сетка

12-колоночная CSS Grid через `.site-shell` / `.site-shell__full` (`site.css`). Карточка — `span 3` (4 в ряд на desktop).

Стили сетки работ на главной — **inline** в `<style>` внутри `index.html` (не только `site.css`).

---

## Навигация

На всех внутренних страницах угловая навигация рендерится автоматически через `site.js` (функция `renderCornerNav`).

Четыре угла экрана:

| Угол | Содержимое |
|------|------------|
| **NW** | Julie Arkhipova → главная; Instagram, LinkedIn, Behance |
| **NE** | Work, Index, Research, Playground, About, CV |
| **SW** | Email (клик копирует `arkhipoovau@gmail.com`) |
| **SE** | Слоган *«This is a celebration, not a tournament»* → About |

Активный раздел подсвечивается по атрибуту `data-page` на `<body>`:

```html
<body data-page="about">
```

Для страниц кейсов используется `data-page="project"` — в NE-меню ничего не активно, ссылка **Work** ведёт на главную.

**Важно:** угловая навигация рендерится **только если** на `<body>` есть `data-page`. Страницы без этого атрибута (например `refs.html`) — без corner nav.

На странице кейса есть локальная ссылка **Work** в шапке (`project-header__back`).

---

## Ключевые файлы

```
arkhipovau/
├── index.html              # Главная
├── site.css                # Глобальные стили, типографика, motion, все страницы
├── site.js                 # Угловая навигация, оверлеи, toast, page enter
├── MANUAL.md               # Этот файл
├── references.md           # Дизайн-референсы и заметки по типографике
│
├── about/
├── cv/
├── research/
├── playground/
├── index/                  # Vanderbrand project index
├── {project-slug}/         # Кейсы (генерируются скриптом)
│
├── assets/images/
│   ├── manifest.json       # Пути к изображениям по slug
│   ├── card-heroes.json    # Hero-картинки для карточек на главной
│   ├── playground-images.json  # Маппинг позиций (reference, playground inline)
│   ├── main/               # Hero-изображения с homepage Readymag
│   └── favicon.png
│
├── maison/                 # Design lab Margiela: preview.html, tokens, fonts
├── refs.html               # Индекс всех скачанных референс-сайтов
├── references-fetch.json   # Метаданные загрузки референсов
├── scripts/
│   ├── download-readymag-images.py
│   ├── build-project-pages.py
│   └── convert-images.py
│
└── {vanderbrand, mouthwash, …}/   # Скачанные референс-сайты (не часть продакшена)
```

---

## Index (`index/index.html`) — таблица Vanderbrand

- Кастомные элементы `<accordion-element>` — раскрывающиеся строки
- Сортировка по **Project / Type / Year** (клик по заголовку колонки, повторный — смена asc/desc)
- Длинные названия: marquee при overflow (`.vb-marquee`)
- Превью внутри строки — из `manifest.json` / `card-heroes.json`
- Ссылка **View project** открывается в **новой вкладке** (`target="_blank"`)
- Footer: Office Hours + **живые часы EST** (`America/New_York`)
- `<body data-page="index">`

---

## Playground

- 13 экспериментов — массив `items` inline в `playground/index.html`
- Полноэкранный viewer (`100svh`), scroll body заблокирован
- Навигация: стрелки, табы, клавиши ← → ↑ ↓
- Картинки: `assets/images/playground/` (jpg + png)
- `<body data-page="playground">`

---

## Research

- Карусель из 2 эссе — массив `essays` в `research/index.html`
- Autoplay 8s, pagination bullets, counter
- Ссылки ведут на локальные long-form страницы эссе
- `<body data-page="research">`

---

## Страницы кейсов (`{slug}/index.html`)

**Генерируются скриптом** — ручные правки в HTML **перезапишутся** при следующем `build-project-pages.py`.

Чтобы изменить контент кейса:

1. Править на Readymag / arkhipovau.xyz → перезапустить download + build, **или**
2. Менять логику/шаблон в `scripts/build-project-pages.py`

Шаблон: заголовок, год, Role/Discipline/Team, lead, стопка figure + prose. Research-эссе — класс `page-main--essay`, секции с `<h2>`.

---

## Типографика

Модель Margiela — **2 семейства, 3 размера sans, weight 400**:

| Токен | Размер | Класс |
|-------|--------|-------|
| Menu | 14px / lh 20 | `.type-menu` |
| Body | 16px / lh 24 | `.type-body` |
| Meta | 13px / lh 18 | `.type-meta` |

Serif (Georgia) — `.type-serif` для лидов и длинных текстов.

Шрифты: `maison/fonts/SuisseIntl-Regular.otf`, `SuisseIntl-RegularItalic.otf`.

CSS-переменные в `:root` файла `site.css` (и дубли в `maison/tokens.css`).

---

## Анимация

Токены motion в `site.css`:

```css
--motion-fast: 200ms;
--motion-base: 400ms;
--motion-slow: 650ms;
--motion-ease: cubic-bezier(0.25, 0.1, 0.25, 1);
```

- Вход страницы: fade + лёгкий slide-up на `.page-main`, `.portfolio`, `.vb-page`
- Оверлеи: fade, body scroll lock (`.is-locked`)
- Фильтр работ на главной: краткое затемнение (`.is-filtering`)
- `prefers-reduced-motion: reduce` — анимации отключаются

`site.js` добавляет `body.is-page-ready` после загрузки.

---

## Скрипты и пайплайн контента

### 1. Скачать изображения с оригинала

```bash
python3 scripts/download-readymag-images.py
```

- Читает `https://arkhipovau.xyz/`
- Для каждого slug качает картинки из Readymag HTML-snippet
- Сохраняет в `assets/images/{slug}/`
- Обновляет `assets/images/manifest.json`

**Примечание:** cover-скриншоты с CDN Readymag иногда отдают HTTP 403 — это известное ограничение.

### 2. Сгенерировать страницы кейсов

```bash
python3 scripts/build-project-pages.py
```

- Парсит текст и порядок блоков из Readymag snippets
- Берёт пути к картинкам из `manifest.json`
- Пишет `{slug}/index.html` для всех slug в manifest (кроме `playground`)

После правок на arkhipovau.xyz: сначала `download-readymag-images.py`, потом `build-project-pages.py`.

**Требуется интернет** — скрипты тянут HTML с Readymag CDN.

**Не редактировать вручную** `{slug}/index.html` — только через build-скрипт (см. выше).

### 3. Конвертация изображений (опционально, не включено в WIP)

```bash
python3 scripts/convert-images.py --format webp --update-manifest
# или AVIF:
python3 scripts/convert-images.py --format avif --crf 18 --update-manifest
```

Требует `ffmpeg` (AVIF) или `cwebp` (WebP). Пока не применено к продакшен-ассетам.

---

## Как добавить новый проект

1. Опубликовать страницу на Readymag / добавить в arkhipovau.xyz.
2. Запустить `download-readymag-images.py` — появится папка и запись в manifest.
3. Запустить `build-project-pages.py` — появится `{slug}/index.html`.
4. Добавить карточку в массив `projects` в `index.html` (поля: `title`, `tags`, `line`, `uri`, `discipline`, `zone`).
5. При необходимости — строку в `index/index.html` (title, type, year, uri).
6. Опционально — hero в `assets/images/card-heroes.json`.

Ссылки на главной: `/${uri}/` (от корня сайта).  
В Index: `../${uri}/`.

---

## Редактирование без скриптов

| Что менять | Где |
|------------|-----|
| Тексты About | `about/index.html` |
| CV | `cv/index.html` |
| Список эссе Research | `research/index.html` → массив `essays` |
| Эксперименты Playground | `playground/index.html` + `assets/images/playground-images.json` |
| Карточки на главной | `index.html` → `projects`, `workItem()` |
| Таблица Index | `index/index.html` → `projects` |
| Глобальные стили | `site.css` |
| Навигация, оверлеи | `site.js` |

---

## WIP — что ещё не готово

### Контент и страницы

- [ ] Локальные страницы для проектов **Soon** (Crim, Blanc, Chichilaki, Veter Magazine и др.)
- [ ] `biomed`, `splat-smilex`, `splat-special` — страницы есть, но не в главной / Index
- [ ] Полная верность оригиналу Readymag — упрощённый шаблон кейса, не pixel-perfect
- [ ] Research-эссе — без оглавления / якорной навигации как на оригинале
- [ ] Cover-изображения проектов (403 с CDN)
- [ ] Форма Stay in touch — заглушка через mailto, нет подписки / CRM

### Дизайн и UX

- [ ] Выбор layout для шапки CV (exploration в Cursor canvas — не внедрён в `cv/index.html`)
- [ ] WebP/AVIF для всех ассетов
- [ ] Деплой / хостинг (сейчас только локальный `http.server`)
- [ ] `cv/index.html` всё ещё ссылается на `arkhipovau.xyz` в одном месте
- [ ] Index: «View project» открывается в новой вкладке — возможно стоит same-tab
- [ ] Часть inline-стилей на главной ещё в `index.html`, не вынесена в `site.css`

### Техническое

- [ ] Нет CI, тестов, линтеров
- [ ] Нет автоматической синхронизации с Readymag — только ручной запуск скриптов
- [ ] Папки `{mouthwash, vanderbrand, …}` — архив референсов, не часть сайта
- [ ] Язык UI — English; мануал — RU
- [ ] Email в коде: `arkhipoovau@gmail.com` (с двумя «o») — проверить, intentional ли

### Сделано (для ориентира)

- [x] Главная с фильтром Branding / Product / Research
- [x] Index-таблица Vanderbrand
- [x] About, CV, Research, Playground
- [x] 14 локальных страниц кейсов с оригинальным текстом и картинками
- [x] Угловая навигация + типографика Margiela
- [x] Система motion + `prefers-reduced-motion`
- [x] Скрипты download + build

---

## Частые задачи

**Обновить кейс после правок на Readymag:**

```bash
python3 scripts/download-readymag-images.py
python3 scripts/build-project-pages.py
```

**Поменять email / соцсети:**  
`site.js` (corner NW), `about/index.html`, `index/index.html` footer.

**Поменять слоган:**  
`site.js` → `tagline`, также на About как splash.

**Сайт «не обновился»:**  
Cmd+Shift+R; проверить, что сервер запущен из корня `arkhipovau/`, а не из подпапки.

**Порт 8080 занят:**

```bash
python3 -m http.server 8081
# → http://localhost:8081
```

---

## Git и деплой

- Коммиты создаются **только по явной просьбе** — проект в активной разработке.
- Перед деплоем: прогнать build-скрипты, проверить все slug вручную, решить WIP-пункты выше.

---

## Связанные документы

- `references.md` — разбор референс-сайтов, типографика, связь с arkhipovau.xyz (RU)
- `refs.html` — индекс ~20 локальных snapshot-референсов (Maison, Vanderbrand, Mouthwash, 1/1, …)
- `maison/preview.html` — sandbox типографики Margiela (не продакшен)

---

## Репозиторий

Рабочая папка сайта: `arkhipovau/` внутри workspace. Git может быть инициализирован на уровень выше (`~/arkhipovau`) — перед commit смотри `git status` из нужной директории.

---

## Контакты в проекте

- Email: `arkhipoovau@gmail.com` (копируется по клику в SW-углу)
- Instagram: [@arkhipovau](https://www.instagram.com/arkhipovau/)
- LinkedIn: [arkhipovau](https://www.linkedin.com/in/arkhipovau/)
- Behance: [arkhipovau](https://www.behance.net/arkhipovau)
