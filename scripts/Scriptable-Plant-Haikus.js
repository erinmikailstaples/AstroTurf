// Scriptable Plant Haikus
// Load this file in the Scriptable app on iOS.
// It shows a silly rotating set of plant-themed haikus.

// If running inside Scriptable, global objects like ListWidget and Script are available.
// If you open this in Node, we provide a tiny shim so you can preview output.

(async function main() {
  const haikus = [
    // 5-7-5-ish. Slightly silly, always botanical.
    [
      "Moss on quiet stone",
      "whispers photosynthesis",
      "gnomes nod approving"
    ],
    [
      "Sunflower tall, bold",
      "tracks meetings across the sky",
      "minutes become seeds"
    ],
    [
      "Fern curls like question",
      "unfurls answers at sunrise",
      "shade applauds softly"
    ],
    [
      "Cactus keeps receipts",
      "of every drop ever spent",
      "budget: succulent"
    ],
    [
      "Mint invades the pot",
      "writes forked roots into history",
      "tea accepts the PR"
    ],
    [
      "Bamboo push commits",
      "fast green continuous deploy",
      "pandas run the tests"
    ],
    [
      "Dandelion puff",
      "issues opened to the wind",
      "labels: wish, pending"
    ],
    [
      "Aloe, calm and cool",
      "handles hotfixes with gel",
      "blameless root-cause: sun"
    ],
    [
      "Thyme takes its own time",
      "schedules flavor in sprints",
      "retros taste better"
    ],
    [
      "Peony debugs",
      "petals step through perfumed code",
      "spring ships v1.0"
    ],
  ];

  const grassEmoji = ["🌱", "🌿", "🍃", "🌵", "🌼", "🌷", "🌾", "🌻"];  
  const choice = (arr) => arr[Math.floor(Math.random() * arr.length)];

  const pickHaiku = () => choice(haikus);

  const title = `${choice(grassEmoji)} Plant Haiku`;
  const [l1, l2, l3] = pickHaiku();
  const footer = "tap to cycle—water your code";

  // Scriptable widget UI
  if (typeof ListWidget !== "undefined") {
    const widget = new ListWidget();
    widget.setPadding(12, 12, 12, 12);
    widget.backgroundGradient = (() => {
      const g = new LinearGradient();
      g.colors = [new Color("#E8F5E9"), new Color("#C8E6C9")];
      g.locations = [0, 1];
      return g;
    })();

    const titleTxt = widget.addText(title);
    titleTxt.font = Font.semiboldSystemFont(13);
    titleTxt.textColor = new Color("#1B5E20");

    widget.addSpacer(6);

    const line1 = widget.addText(l1);
    line1.font = Font.regularMonospacedSystemFont(12);
    line1.textColor = new Color("#2E7D32");

    const line2 = widget.addText(l2);
    line2.font = Font.regularMonospacedSystemFont(12);
    line2.textColor = new Color("#2E7D32");

    const line3 = widget.addText(l3);
    line3.font = Font.regularMonospacedSystemFont(12);
    line3.textColor = new Color("#2E7D32");

    widget.addSpacer(8);

    const foot = widget.addText(footer);
    foot.font = Font.italicSystemFont(10);
    foot.textColor = new Color("#388E3C");

    // Tap to refresh by re-running the same script
    if (typeof Script !== "undefined") {
      const fileName = Script.name();
      widget.url = `scriptable:///run/${encodeURIComponent(fileName)}`;
    }

    if (config.runsInWidget) {
      Script.setWidget(widget);
    } else {
      await widget.presentSmall();
    }
    Script.complete();
    return;
  }

  // Fallback for Node preview (repo context). Prints a boxed haiku.
  const box = (s) => `\n${"=".repeat(36)}\n${s}\n${"=".repeat(36)}\n`;
  const lines = [title, "", l1, l2, l3, "", footer].join("\n");
  console.log(box(lines));
})();

