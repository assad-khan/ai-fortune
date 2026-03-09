AI Fortune-Telling Booth Concept
We propose building an interactive booth where a camera “reads” a visitor’s palm and an on-screen AI avatar verbally delivers a fortune. This leverages existing avatar/video-generation platforms and hand-tracking technology. Below we survey the key components, integration approaches, costs, and development effort.

1. Avatar Platforms & API Costs
Several commercial AI video/avatar platforms can generate a talking avatar from text scripts. Key options:

HeyGen – A leading avatar video API. The API Pro plan is 100 credits ($99/mo)[1]. Each credit yields ~1 minute of video (with the “Video Avatars Unlimited” engine)[1]. Thus 100 credits ≈ 100 min of content (≈ 1 min per reading). A larger Scale plan is 660 credits for $330/mo[2]. (HeyGen also offers LiveAvatar streaming: $100 buys 1000 credits[3]; custom SDKs use 1 credit/min of streaming[4].) HeyGen’s starter plan is effectively one free credit, with paid plans from ~$29/mo[5]. HeyGen has 700+ avatar/voice options and supports 40+ languages[6]. It also offers Custom/Digital-Twin Avatars (from photos) in higher tiers[7].
Synthesia – Industry-standard video avatars. Synthesia’s Personal plan (~$89/year) allows ~10 min video; a Business plan ($22–89/mo) unlocks more minutes and custom avatars[8][9]. Synthesia supports up to 140+ avatars and 120+ languages[8]. (Notably, Synthesia’s Creator tier ($89/mo) includes 5 personal avatars[9].) However, entry pricing is higher and API access is typically enterprise-level, making it costlier per minute than HeyGen.
D-ID (Creative Reality) – Another AI avatar service. D-ID’s studio “Lite” plan is about \$5.90/mo (billed annually) and includes limited minutes[10]. Pro is ~$49/mo, Advanced ~$299/mo[10]. D-ID’s API offers video minutes (deducted by 15 s increments) and can produce photoreal avatars from photos. It provides up to 30+ language voices. A 14-day free trial with watermark is available[10].
Elai.io – AI video platform (powered by Panopto). Their Creator plan is ~$67/mo for 60 min, Custom plan $3000/yr. They allow custom “Selfie Avatars” ($199/yr) from user footage. (More expensive than HeyGen for similar use.)
Other – Tools like Character Animator/Unity (hand-animated puppets) or MetaHuman/Unreal Engine are possible but require heavy custom dev (animators, rigging) and are not as turnkey. We focus on off-the-shelf AI avatar APIs for speed and cost-effectiveness.
Cost Example: At 1 min per reading, HeyGen Pro costs ~$0.99 per session (100 credits/100 min). HeyGen Scale drops it to ~$0.50/min[1]. Synthesia is ~$18 for 10 min (starter) = \$1.80/min[8]. D-ID Lite’s minutes are cheaper (few cents/min). Live streaming (HeyGen LiveAvatar custom) could be ~$0.10/min[4] if needed.

2. Palm-Reading Input Methods
To “read” a palm, the system needs to detect a hand and optionally interpret palm features. In practice, full palmistry (identifying life, heart, fate lines) is complex; we likely simplify to image capture + trigger. Key approaches:

Hand-Tracking Libraries: Google’s MediaPipe Hand Landmarker can detect palm and finger joints in real-time from a camera feed[11]. It outputs 21 hand landmarks per frame[11]. Using a smartphone or webcam, the user places their palm in view and MediaPipe confirms a hand is present. (This could be done in-browser via MediaPipe.js or on a local Python backend.)
Mobile AR/Computer Vision: On iOS, ARKit (Vision framework) supports hand pose detection; on Android, TensorFlow (or handpose models) can be used. These are less common than MediaPipe but possible.
Dedicated Sensors: Leap Motion (Ultraleap) or Intel RealSense are USB devices for hand tracking/gestures. These give very robust hand data (e.g. depth mapping of palm lines) but add hardware cost (~\$80–\$200). They might be overkill if a simple camera suffices.
Manual Trigger: The simplest method is to use a camera and button. E.g. user presses “Scan my palm” when their hand is in frame; software snaps an image to simulate “reading”. No actual line analysis is needed if fortunes are randomized or AI-generated.
Once a palm image is captured, you generate a fortune. This could be completely random (pre-written fortunes) or use AI (e.g. send a prompt to a large language model: “User’s palm has these features, give a fortune”). Some online services (e.g. Palmist.io[12]) claim to analyze palm lines via AI. We may skip deep palmistry: instead, the booth could simply say “studying the lines… your Fate line is very long” etc., based on simple rules or pure randomness. (Even if not real, it creates the effect.) A fallback is to use an LLM (e.g. GPT) to craft a personalized message given static palm facts, though GPT cannot analyze an image without vision input. Overall, camera detection (e.g. MediaPipe) ensures the palm is in place; fortune text can come from a fixed script or AI text API.


Figure: The user places their palm under the camera. Hand-tracking (e.g. Google MediaPipe[11]) can confirm the palm is visible, then a fortune is generated.

3. Ensuring a Consistent Avatar
The avatar’s identity should remain constant across sessions. Approaches:

Pre-Selected Avatar ID: With HeyGen (or Synthesia), you simply pick one avatar (e.g. “Fortune Teller Avatar #5”) and specify it in every API call. This ensures the same face/voice each time. HeyGen provides 700+ avatars and “Looks” to choose a mystic style[6].
Custom Avatar: For branding or uniqueness, create one custom avatar (a digital twin) from photos/videos of a model. HeyGen’s “Custom Avatar” feature can build a likeness, and you would then use that avatar ID in API calls[7]. (Note: via API this requires an Enterprise subscription[13], but one could pre-create it via HeyGen Studio.) Similarly, Synthesia and D-ID offer “personas” but often at higher cost.
Avatar Voice: Once the avatar is chosen, its voice remains fixed by selecting one voice ID. For variety, you can tweak pitch/emotion, but we likely keep the same voice for consistency.
Animation & Interaction: HeyGen avatars come pre-rigged with mouth/body animation driven by the generated speech. If using LiveAvatar streaming, the avatar could even react in real-time (varying gestures), though that requires a continuous stream. For simplicity, we will probably pre-generate each 1-minute answer video and then play it.
[7] specifically notes: “HeyGen’s Custom Avatar feature can create a digital twin from [your own] photos and videos… You can even customize your avatar’s look… to match your mystical branding.” By reusing that same avatar ID (or any chosen Public Avatar) for each fortune reading, the booth’s avatar remains the same person every time.

4. Implementation Steps
A high-level integration plan:

Camera & UI (Frontend): Set up a display+camera (could be a kiosk/tablet or laptop). A simple UI invites the user, shows camera feed, and has a “Scan Palm” button. When pressed, the system either immediately captures the image or waits until MediaPipe confirms a palm is in frame[11].
Palm Detection: Use MediaPipe Hands (Python or JavaScript) to detect landmarks. If confidence is high (≥50–70%), accept and proceed. This ensures the user actually placed their palm.
Fortune Generation: Once a palm image is captured, generate the fortune text. Options:
Random/Prewritten: Choose from a predefined list of fortunes. This is simplest and requires no API.
AI Text (Optional): Send relevant cues (e.g. “Your Life line looks long; what is the fortune?”) to a large language model (ChatGPT API) to create a unique message. (This requires internet and incurs a small token cost, but can add novelty.)
Video Avatar Generation (HeyGen API): With the fortune text ready, call HeyGen’s Text-to-Video API: send the chosen avatar ID, voice ID, and the script. HeyGen returns a video (URL or binary) of the avatar speaking the fortune (and performing any gestures). This usually takes a few seconds per minute of video.
Playback: Play the generated video on the booth screen to the user. Optionally add background music or on-screen graphics (HeyGen templates could include tarot visuals). After playback, the system can reset and prompt the next user.
Optional – Pre-Generate Library: If many fortunes are fixed, you could pre-generate all combinations (or many) and store them. Then the booth just randomly selects a ready video instead of calling the API each time. This trades storage for realtime cost and latency.
Backend Infrastructure: A lightweight server (Node/Python) to host the Web UI, run MediaPipe (if not on-device), call HeyGen (and any AI API), and serve/play the video. This could run on the kiosk machine itself (offline mode) or in the cloud (if the booth has reliable internet).
Data Logging/Analytics (optional): Record which fortunes were given, or user interactions, for analytics or future improvements.
5. Integration Options – Live vs Pre-Recorded
On-Demand Video (API): Each time, generate a new video via HeyGen API. Simpler to implement (batch-style) and flexible but incurs some wait (~5-10s for a ~1min clip)[14]. Requires internet for the API call, but allows truly personalized text each session.
Streaming Avatar (LiveAvatar): Use HeyGen LiveAvatar SDK for real-time conversation. Here the avatar is like a live host – you send text in real-time and it speaks immediately. This can be more engaging (avatar can change gaze/gesture dynamically) but is more complex: you need to maintain an active session and consume credits continuously (2 credits/min for full SDK)[4]. Also needs robust internet. It’s ideal for interactive chatbots, but for a kiosk where the conversation is one-way (avatar speaks a prepared line), the video-API approach is simpler and cheaper per session (about 1 credit/min vs 2).
Given the use case (user asks for a fortune, the avatar reads a one-minute fortune and stops), pre-recorded API videos are likely sufficient and easier. We can hide generation time with an animated “processing” screen, then play the video. If the client wanted live engagement (e.g. follow-up Q&A), the LiveAvatar route could be explored (with costs ~\$0.10–\$0.20 per minute[4]).

6. Estimated Development Effort
Building a complete prototype will require work in several areas. Rough time estimates (assuming a single experienced developer or small team):

Requirements & Design: 5–10 hours (defining features, UI flow, script content).
Avatar Platform Integration: 10–15 hours (HeyGen account setup, API auth, writing code to send scripts and retrieve videos, handling quotas and errors).
Front-End & Camera UI: 15–20 hours (create a simple touchscreen UI or web page, integrate camera feed and “scan” button, handle image capture).
Hand/Palm Detection: 10–15 hours (integrating MediaPipe or similar, tuning detection thresholds, testing on various hand positions).
Fortune Logic: 5–10 hours (drafting fortune text, coding selection or AI prompt logic, plus translation if needed).
Video Playback & Experience: 5–10 hours (play video, add countdown/backdrop, handle user flow and reset).
Testing & Refinement: 10–15 hours (UX polishing, edge cases, multiple devices).
Project Management/Communication: 5–10 hours (meetings, documentation).
(Optional) Offline/Cloud Setup: 5–10 hours (deploying backend if cloud-based, or configuring kiosk machine; ensuring internet bandwidth).
Total: ~50–75 man-hours for an MVP. A more polished product (animations, error handling, multilingual, live avatar features) could push 100+ hours. If using LiveAvatar streaming, add another ~15–20 hours for integration testing.

7. Running Costs
Avatar API subscription: If usage is moderate (e.g. ~100 readings per month), a HeyGen Pro ($99/mo) might suffice (100 credits). For heavier use, HeyGen Scale ($330/mo) gives 660 credits. Alternatively, D-ID Pro ($16/mo) with 60 min might work but has watermarks on lower plans. Plan conservatively: ~$100–300/month for avatar service, depending on expected footfall.
Cloud/Server: If the booth has internet, we might host the backend on a small cloud VM (e.g. AWS EC2, Azure, or similar). A t3.small (or equivalent) with Python/Node and camera handling could be ~$30–50/month. (Alternatively, run everything on a local PC; cost then is zero except electricity.)
AI Services (optional): If using ChatGPT or voice APIs, costs are minimal. E.g. OpenAI’s GPT-3.5 is ~$0.002 per 1K tokens[15] – less than \$0.01 per query typically. Custom voices (like ElevenLabs) cost a few dollars per 1M chars, also minor for short fortunes.
Hardware: One-time costs: camera ($50–100), touchscreen/display ($200–400), a small PC ($500) if not using an existing device. These are one-off and not counted in monthly.
Example Run Cost: If we run 100 sessions/day (3000/mo) at 1 min each, that’s 3000 minutes = 3000 HeyGen credits = need Scale plan and some extra. 3000 credits ~ \$1500/month (Scale+ overage) – likely too high. For lighter use (1000 sessions/mo), 1000 credits (\$330/mo scale plan covers 660, plus one extra pro or overage). So budget \$100–\$500/mo depending on traffic.

8. Conclusion
In summary, this AI fortune-telling booth is fully viable with current technology. We recommend using a platform like HeyGen for the speaking avatar (it offers a rich avatar library and straightforward API)[14][7]. The user interface can simply use camera-based hand detection (e.g. Mediapipe[11]) to trigger the experience. Development on a small team (~2–3 weeks of work) should suffice to deliver a polished demo.

Key citations: We draw on HeyGen’s documentation for pricing (e.g. \$99/100 credits[1]) and avatar features[7], industry comparisons for relative costs[10], and Google’s hand-tracking info[11].

Sources: HeyGen API docs[14][3]; HeyGen community tutorial[7]; Synthesia pricing page[8][9]; D-ID/Tavus comparison[10]; MediaPipe hands overview[11]; Palmist site[12]. (Costs and plans are as of early 2026 and subject to change.)

[1] [2] [3] [4] [13] [14] HeyGen API / LiveAvatar Pricing & Subscriptions Explained | HeyGen Help Center

https://help.heygen.com/en/articles/10060327-heygen-api-liveavatar-pricing-subscriptions-explained

[5] [10] The top 3 D‑ID alternatives

https://www.tavus.io/post/the-top-d-id-alternatives

[6] [7] How to use HeyGen for fortune-telling and astrology - Guide | HeyGen

https://community.heygen.com/public/resources/how-to-use-heygen-for-fortune-telling-and-astrology

[8] [9] Synthesia Pricing - Compare Free and Paid Plans

https://www.synthesia.io/pricing

[11] layout: forward target: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker title: Hands parent: MediaPipe Legacy Solutions nav_order: 4 — MediaPipe v0.7.5 documentation

https://mediapipe.readthedocs.io/en/latest/solutions/hands.html

[12] Palmist - AI Powered Palm Reading

https://palmist.io/

[15] Pricing | OpenAI API

https://developers.openai.com/api/docs/pricing/