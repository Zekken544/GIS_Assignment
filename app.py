"""Build an offline evidence dashboard for riverbank and fence change."""
from base64 import b64encode
from dataclasses import dataclass
from html import escape
from pathlib import Path
from math import floor, ceil, isfinite
import csv
import json
import re
import sys
from struct import unpack

ROOT = Path(__file__).resolve().parent
COLORS = ("#126c69", "#9a451f", "#405ba6", "#6a4e90", "#826412", "#af325e")

# Years and months are supplied with the photographs.
CAPTIONS = {
    "2011": "Хашааны дагуу цайвар зурвас болон замын мөр харагдана.",
    "2017": "Тохойн гадна талын хашаа, эргийн завсар дахь зурвас харагдана.",
    "2020": "Нэг хэсэгт хашаа, голын хооронд цайвар зурвас харагдана.",
    "2021-07": "Хашааны дагуу зарим хэсэгт нарийн цайвар зурвас харагдана.",
    "2021-09": "Ус хашааны ойролцоо харагдана. Энэ үеийн усны зах нь эргийн дээд ирмэгийг төлөөлөхөд тохиромжгүй.",
    "2022": "Тохойн зарим хэсэгт хашаа, эргийн завсар нарийн хэвээр харагдана.",
    "2026": "Хэрэглэгчийн мэдээллээр эзэмшигч хашаагаа голоос холдуулсан. Зураг дээр хэд хэдэн хэсэгт хашааны шугам өөрчлөгдсөн байна.",
}


@dataclass(frozen=True)
class Transect:
    identifier: str
    y: float


@dataclass(frozen=True)
class Position:
    transect_id: str
    bank_x: float | None
    fence_x: float | None

    @property
    def width_px(self):
        if self.bank_x is None or self.fence_x is None or self.fence_x < self.bank_x:
            return None
        return self.fence_x - self.bank_x


@dataclass(frozen=True)
class Observation:
    date: str
    filename: str
    quality: str
    positions: tuple[Position, ...]


@dataclass(frozen=True)
class Study:
    reference: str
    units: str
    transects: tuple[Transect, ...]
    observations: tuple[Observation, ...]


def coordinate(value, *, nullable=False):
    if value is None and nullable:
        return value
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError("Координат тоон утга эсвэл null байна.")
    return float(value)


def load_study(path):
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if raw["units"] != "reference_px":
        raise ValueError("Координатын нэгж reference_px байна.")
    transects = tuple(Transect(t["id"], coordinate(t["y"])) for t in raw["transects"])
    identifiers = [t.identifier for t in transects]
    if not identifiers or len(set(identifiers)) != len(identifiers):
        raise ValueError("Огтлолын дугаар давхцахгүй байна.")
    dates = set()
    observations = []
    for row in raw["observations"]:
        date = row["date"]
        if not isinstance(date, str) or not re.fullmatch(r"\d{4}(?:-(?:0[1-9]|1[0-2]))?", date) or date in dates:
            raise ValueError(f"Огноо давхардсан эсвэл хэлбэр буруу: {date}")
        dates.add(date)
        points = {}
        for point in row["points"]:
            identifier = point["id"]
            if identifier not in identifiers or identifier in points:
                raise ValueError(f"{date} огнооны огтлолын дугаар буруу: {identifier}")
            points[identifier] = Position(
                identifier,
                coordinate(point["bank_x"], nullable=True),
                coordinate(point["fence_x"], nullable=True),
            )
        positions = tuple(points.get(identifier, Position(identifier, None, None)) for identifier in identifiers)
        observations.append(Observation(date, row["filename"], row["quality"], positions))
    if not observations or raw["reference"] not in dates:
        raise ValueError("Лавлах огноо ажиглалтын жагсаалтад байна.")
    return Study(raw["reference"], raw["units"], transects, tuple(sorted(observations, key=lambda o: o.date)))


def label(value):
    return f"{value:.0f}" if value is not None else ""


def write_csv(study, path):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["date", "transect", "reference_y_px", "bank_x_px", "fence_x_px", "width_px", "quality"])
        for observation in study.observations:
            for transect, point in zip(study.transects, observation.positions):
                writer.writerow([
                    observation.date, transect.identifier, label(transect.y), label(point.bank_x),
                    label(point.fence_x), label(point.width_px), observation.quality,
                ])


def profiles(study):
    dates = [obs.date for obs in study.observations]
    width = max(890, 120 + 90 * len(dates))
    height = 700
    x0, x1 = 86, width - 38
    spacing = (x1 - x0) / max(1, len(dates) - 1)
    xs = [x0 + i * spacing for i in range(len(dates))]
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
        '<title id="title">Эрэг, хашаа, зурвасын өргөн</title>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        '<style>text{font:13px Arial,sans-serif;fill:#243b3e}.title{font-size:19px;font-weight:bold}.note{fill:#495c60}</style>',
    ]
    for index, transect in enumerate(study.transects):
        x = 40 + index * 100
        color = COLORS[index % len(COLORS)]
        output.append(f'<circle cx="{x}" cy="27" r="5" fill="{color}"/>')
        output.append(f'<text x="{x + 12}" y="31">{escape(transect.identifier)}</text>')
    panels = [
        ("bank_x", "Эрэг талын тэмдэглэсэн ирмэгийн X байрлал"),
        ("fence_x", "Харагдах хашааны X байрлал"),
        ("width_px", "Хашаа ба эрэг талын ирмэг хоорондын өргөн"),
    ]
    for panel_index, (attribute, title) in enumerate(panels):
        top = 82 + panel_index * 198
        bottom = top + 126
        output.append(f'<text class="title" x="37" y="{top - 19}">{title}</text>')
        values = [getattr(p, attribute) for o in study.observations for p in o.positions
                  if getattr(p, attribute) is not None]
        if not values:
            output.append(f'<text x="37" y="{top + 34}">Хангалттай тод хэмжилт байхгүй</text>')
            continue
        low, high = min(values), max(values)
        step = max(5, ceil((high - low) / 20) * 5)
        low = floor(low / step) * step
        high = max(low + step, ceil(high / step) * step)
        for mark in range(low, high + 1, step):
            y = bottom - (mark - low) * (bottom - top) / (high - low)
            output.append(f'<line x1="{x0 - 12}" x2="{x1 + 15}" y1="{y:.1f}" y2="{y:.1f}" stroke="#dce6e4"/>')
            output.append(f'<text x="{x0 - 19}" y="{y + 4:.1f}" text-anchor="end">{mark}</text>')
        for x, observation in zip(xs, study.observations):
            output.append(f'<text x="{x}" y="{bottom + 23}" text-anchor="middle">{escape(observation.date)}</text>')
            count = len(observation.positions)
            for i, point in enumerate(observation.positions):
                value = getattr(point, attribute)
                if value is None:
                    continue
                cx = x + (i - (count - 1) / 2) * 9
                cy = bottom - (value - low) * (bottom - top) / (high - low)
                color = COLORS[i % len(COLORS)]
                tooltip = f"{observation.date} / {point.transect_id}: {label(value)} px"
                output.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" fill="{color}" stroke="#fff">'
                              f'<title>{escape(tooltip)}</title></circle>')
    output.append('<text class="note" x="37" y="682">Лавлах пиксел · X баруун тийш өснө · Огнооны зай тэнцүү дүрслэгдсэн</text>')
    output.append("</svg>")
    return "\n".join(output)


def reference_overlay(study):
    observation = next(o for o in study.observations if o.date == study.reference)
    source = (ROOT / "images" / observation.filename).read_bytes()
    width, height = unpack(">II", source[16:24])
    encoded = b64encode(source).decode("ascii")
    output = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">',
        f'<title id="title">{study.reference} оны лавлах зураг ба хөндлөн огтлолууд</title>',
        f'<image width="{width}" height="{height}" href="data:image/png;base64,{encoded}"/>',
        '<style>text{font:bold 15px Arial,sans-serif;fill:white;paint-order:stroke;stroke:#16312d;stroke-width:3px}</style>',
    ]
    for transect, point in zip(study.transects, observation.positions):
        values = [x for x in (point.bank_x, point.fence_x) if x is not None]
        if not values:
            continue
        left, right = max(0, min(values) - 33), min(width, max(values) + 30)
        y = transect.y
        output.append(f'<line x1="{left}" x2="{right}" y1="{y}" y2="{y}" stroke="#fff" stroke-width="2" stroke-dasharray="5 3"/>')
        if point.width_px is not None:
            output.append(f'<line x1="{point.bank_x}" x2="{point.fence_x}" y1="{y}" y2="{y}" stroke="#ffde83" stroke-width="4"/>')
        for x, color in [(point.bank_x, "#86e4db"), (point.fence_x, "#ff9f5b")]:
            if x is not None:
                output.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{color}" stroke="#18312d" stroke-width="1.5"/>')
        output.append(f'<text x="{left - 4}" y="{y + 5}" text-anchor="end">{escape(transect.identifier)}</text>')
    return "\n".join([*output, "</svg>"])

def render_report(study):
    figures = []
    for date, caption in CAPTIONS.items():
        if not (ROOT / "images" / f"{date}.png").is_file():
            continue
        heading = date + (" · Дүрслэлийн лавлагаа" if date == "2017" else "")
        figures.append(
            f'<figure><img src="../images/{date}.png" alt="{date} оны Дэлгэрмөрөн голын тохой">'
            f'<figcaption><strong>{heading}</strong><p>{escape(caption)}</p></figcaption></figure>'
        )
    columns = ("Огноо", "Огтлол", "Эргийн ирмэгийн X", "Хашааны X", "Зурвасын өргөн", "Тэмдэглэл")
    header = "".join(f'<th scope="col">{column}</th>' for column in columns)
    rows = []
    for obs in study.observations:
        for point in obs.positions:
            cells = [obs.date, point.transect_id, label(point.bank_x), label(point.fence_x),
                     label(point.width_px), obs.quality]
            rows.append("<tr>" + "".join(f"<td>{escape(str(value)) if value != '' else '—'}</td>" for value in cells) + "</tr>")
    template = (ROOT / "dashboard.html").read_text(encoding="utf-8")
    first = study.observations[0]
    reference = next(o for o in study.observations if o.date == study.reference)
    shared = [(a.width_px, b.width_px) for a, b in zip(first.positions, reference.positions)
              if a.width_px is not None and b.width_px is not None]
    message = ""
    if shared and first.date != reference.date:
        before = ", ".join(label(pair[0]) for pair in shared)
        after = ", ".join(label(pair[1]) for pair in shared)
        message = (f"<p><strong>{first.date} → {reference.date}</strong> "
                   f"Ижил огтлолуудын харагдах өргөн {before} px-ээс {after} px болж багассан.</p>")
    return (template.replace("{{summary}}", message).replace("{{gallery}}", "\n".join(figures)).replace("{{head}}", header)
            .replace("{{rows}}", "\n".join(rows)).replace("{{reference}}", escape(study.reference)))


def main():
    try:
        study = load_study(ROOT / "data" / "observations.json")
        output = ROOT / "output"
        output.mkdir(exist_ok=True)
        write_csv(study, output / "measurements.csv")
        (output / "reference.svg").write_text(reference_overlay(study), encoding="utf-8")
        (output / "profiles.svg").write_text(profiles(study), encoding="utf-8")
        (output / "report.html").write_text(render_report(study), encoding="utf-8")
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print("Open output/report.html in a browser.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


