import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.utils.html import get_preview_content, get_word_count

# Epic long chapter
long_chapter = """
<h2>Chapter 7: The Long Road Home</h2>
<p>The journey had begun three months ago, though it felt like years. Marcus stood at the edge of the cliff, watching the sun dip below the horizon, painting the sky in shades of orange and purple he'd never seen before. Behind him, the camp was coming alive with the sounds of evening—pots clanging, voices laughing, the crackle of fires being lit.</p>
<p>"Beautiful, isn't it?" Elena's voice came from his left. She'd approached so quietly he hadn't heard her footsteps.</p>
<p>Marcus nodded, not trusting himself to speak. The weight of everything they'd been through sat heavy on his chest. The villages they'd passed through, burned to the ground. The families torn apart. The children with hollow eyes who'd seen too much, too soon.</p>
<p>"I keep thinking about home," Elena continued, moving to stand beside him. "About what it was like before. Do you remember the festivals? The way the whole town would come together?"</p>
<p>"I remember," Marcus said quietly. "My mother used to make those little honey cakes. She'd spend days preparing them."</p>
<p>"Mine too!" Elena laughed, but it was a sad sound. "I wonder if we'll ever have that again. The normalcy of it all. The simple joy of a festival, of knowing everyone you see, of feeling <em>safe</em>."</p>
<p>Marcus turned to look at her properly for the first time in days. Really look at her. The journey had changed them all. Elena's face was thinner, her eyes harder. But there was still that spark in them, that stubborn hope that refused to die no matter what they faced.</p>
<p>"We will," he said with more conviction than he felt. "That's why we're doing this. That's why we keep going."</p>
<p>A shout from the camp interrupted them. Marcus's hand went instinctively to his sword, but it was just one of the younger members of their group, excited about something trivial. They both relaxed.</p>
<p>"I had a dream last night," Elena said after a moment. "We were back home. Everything was rebuilt. Better than before, even. There were new houses, new shops. The old oak tree in the square was still there, somehow survived everything. And people were happy. Actually happy."</p>
<p>"Sounds nice."</p>
<p>"It was. You were there too. You and your mother, selling those honey cakes at the festival. She was teaching some kids how to make them."</p>
<p>Marcus felt his throat tighten. His mother was gone. They both knew it. The enemy had made sure of that. But he didn't correct Elena. Let her have her dream. Let them both have it, for just a moment.</p>
<blockquote><p>Hope is not a strategy, but it's all we have sometimes.</p></blockquote>
<p>The words of their old commander echoed in Marcus's mind. He'd said that right before the final battle, right before everything changed. Right before he'd sacrificed himself so the rest of them could escape.</p>
<p>"We should head back," Marcus said. "Long day tomorrow."</p>
<p>"Always is," Elena agreed. But neither of them moved. They stood there, watching the last of the daylight fade, two people carrying the weight of a world that no longer existed, trying to build something new from the ashes.</p>
<p>Below them, in the valley, Marcus could see the ruins of what had once been a great city. Now it was just broken walls and empty streets. But beyond that, further still, he could see lights. Small villages that had survived. Communities that were rebuilding. Life, somehow, finding a way.</p>
<p>"You know what I miss most?" Elena asked suddenly.</p>
<p>"What?"</p>
<p>"Books. I miss books. Reading stories that someone else wrote, problems that someone else had to solve. Losing myself in pages and pages of words that had nothing to do with survival or strategy or fighting."</p>
<p>Marcus smiled despite himself. "You always did have your nose in a book. Used to drive the training master crazy."</p>
<p>"He got over it when I became one of the best archers in the company."</p>
<p>"Second best," Marcus teased.</p>
<p>"In your <strong>dreams</strong>, Marcus Chen."</p>
<p>For a moment, they were just two kids again, bantering like they used to before the world fell apart. It was a brief respite, a tiny pocket of normalcy in an ocean of chaos. But it was enough. Enough to remind them why they fought. Why they kept going when every logical part of their brains told them to give up.</p>
<p>The stars were beginning to appear now, one by one, tiny pinpricks of light in the darkening sky. Marcus wondered if the same stars shone over what remained of their home. If someone there was looking up at this same sky, hoping for the same things they hoped for.</p>
<p>"Come on," Elena said finally, breaking the spell. "If we don't get back soon, Thomas will eat all the good food again."</p>
<p>"That man has the appetite of three soldiers."</p>
<p>"And the fighting ability of five. We need him."</p>
<p>They walked back to camp together, leaving the cliff and its view behind. But Marcus carried the image with him—that sunset, those ruins, those distant lights. It was a reminder. Of what was lost, yes, but also of what could still be saved. What they were fighting for wasn't just revenge or justice, though those played their part. It was the possibility of honey cakes at festivals. Of books read for pleasure. Of nights where the only worry was whether you'd get your fair share of dinner.</p>
<p>Simple things. Human things.</p>
<p>Worth fighting for.</p>
<p>As they entered the circle of firelight, their companions looked up and smiled. Here, in this moment, they were safe. They were together. And tomorrow, they would take another step toward home. Toward that dream Elena had shared. Toward a future that might, just might, be possible if they refused to give up.</p>
<p>Marcus sat down by the fire, accepted a bowl of stew from Thomas (who grinned at him with that infectious enthusiasm that never seemed to dim), and let himself relax. Just for tonight. Just for now.</p>
<p>The long road home stretched out before them, full of dangers and uncertainties. But they would walk it together. And that made all the difference.</p>
"""

print("\n\n=== LONG CHAPTER ===")
print(f"Word count: {get_word_count(long_chapter)}")
print("\nPreview:")
print(get_preview_content(long_chapter))