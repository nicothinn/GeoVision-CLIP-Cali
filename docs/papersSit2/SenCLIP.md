SenCLIP: Enhancing zero-shot land-use mapping for Sentinel-2 with
ground-level prompting
Pallavi Jain1, 2, 6, Dino Ienco2, 3, 5, 6, Roberto Interdonato2, 4, 5, 6
,
Tristan Berchoux1
and Diego Marcos2, 6
1Mediterranean Agronomic Institute of Montpellier - CIHEAM-IAMM, 2
Inria, 3
INRAE,
4 Cirad, 5 UMR TETIS, 6 Univ. of Montpellier, Montpellier France
{pallavi.jain, dino.ienco, roberto.interdonato, diego.marcos}@inria.fr
berchoux@iamm.fr
Abstract
Pre-trained vision-language models (VLMs), such as
CLIP, demonstrate impressive zero-shot classification capabilities with free-form prompts and even show some generalization in specialized domains. However, their performance on satellite imagery is limited due to the underrepresentation of such data in their training sets, which predominantly consist of ground-level images. Existing prompting techniques for satellite imagery are often restricted
to generic phrases like “a satellite image of. . . ”, limiting their effectiveness for zero-shot land-use/land-cover
(LULC) mapping. To address these challenges, we introduce SenCLIP, which transfers CLIP’s representation
to Sentinel-2 imagery by leveraging a large dataset of
Sentinel-2 images paired with geotagged ground-level photos from across Europe. We evaluate SenCLIP alongside
other state-of-the-art remote sensing VLMs on zero-shot
LULC mapping tasks using the EuroSAT and BigEarthNet
datasets with both aerial and ground-level prompting styles.
Our approach, which aligns ground-level representations
with satellite imagery, demonstrates significant improvements in classification accuracy across both prompt styles,
opening new possibilities for applying free-form textual descriptions in zero-shot LULC mapping. Code, dataset and
pretrained models are available at https://github.
com/pallavijain-pj/SenCLIP
1. Introduction
Monitoring land-use and land-cover (LULC) is essential
for understanding human impacts on the environment and
assessing related risks [41]. Spaceborne sensors have long
been used to map LULC, providing key data for policyrelevant indicators, especially in rural areas [2]. These
insights are crucial for sustainable development, land-use
planning, habitat preservation, and effective natural resource management [7, 9]. During the last decade, the evolution of deep learning has enhanced the reliability of LULC
prediction based on remote sensing [50]. However, these
approaches generally depend on large datasets for training
the models via supervised learning, requiring a large initial
effort and restricting them to a closed set of initial LULC
classes. In general, the class labels influence the learning
process by guiding the optimisation of the network’s parameters towards minimising the classification error for the
known classes [11,14]. Consequently, the network may prioritise learning features that are highly discriminative for
these specific set of classes. This limits the usefulness of
the representation in recognising unseen classes without additional training or fine-tuning steps.
Recent advancements in vision-language models
(VLMs) have revolutionised this paradigm. VLMs leverage
Web-scale image/caption datasets to learn a representation
that allows for zero-shot predictions across various tasks.
These models operate by learning a joint semantic space
for image/text pairs through contrastive learning strategies. Prominent examples of VLMs include CLIP [29],
ALIGN [13], and BLIP [17, 18], which aim to map both
textual descriptions and visual representations into the same
latent space, enabling direct semantic comparisons between
the two modalities. Despite the significant strides made
by VLMs, there are persistent challenges in the practical
implementation of zero-shot approaches based on them.
One of the obstacles lies in the manual prompting process
intrinsic to these approaches, where the choice of vocabulary and specific textual cues for each class play a pivotal
role. Even slight variations in prompt formulation, such
as the inclusion or exclusion of articles like “a” can wield
considerable influence over the model’s accuracy [47].
Moreover, achieving optimal performance often requires
incorporating task-relevant information into the prompts. In
1
arXiv:2412.08536v1 [cs.CV] 11 Dec 2024
specialised domains like remote sensing, specifying details
such as “centered satellite photo” or describing specific
attributes like “photo of {class}: a type of broadleaf forest”
alongside the class name becomes imperative for accurate
classification [1, 29, 47]. This nuanced prompt construction
ensures that the model captures essential contextual cues,
leading to improved classification accuracy [44], even if
the added context is meaningless [31]. The sensitivity of
prompt engineering and prompt learning [46] to a specific
context underscores the critical role of prompting for
harnessing the full potential of VLMs.
Another significant challenge arises when attempting to
move into specialised domains that are underrepresented in
the training sets of VLMs, as is the case in remote sensing
tasks. This results in challenges both for the image representation, which suffers due to the differences to the more
common image modalities in terms of resolution, perspective and radiometry, and the text representation. Indeed, the
CLIP representation of satellite images tends to be aligned
with coarse concepts (e.g. this is a satellite image) that are
of little help for understanding LULC [4]. One potential solution lies in the development of large-scale VLMs specifically tailored for remote sensing applications. However,
a significant obstacle arises due to the scarcity of textual
descriptions associated with remote sensing data. Unlike
other domains with abundant image/text pairs, remote sensing lacks a substantial corpus of annotated satellite imagery
with corresponding textual descriptions.
Recent advancements like RemoteCLIP [22], SkyCLIP [42], and GeoRSCLIP [45] have successfully integrated remote sensing data with captions and class labels
to enhance VLMs. These methods use curated satellite imagery, improving the models’ ability to understand spatial
contexts and semantic relationships through supervised pretraining, leading to better performance. In contrast, labelfree approaches such as Sat2Cap [4] focus on cross-view
learning by integrating geotagged ground-level images with
high-resolution satellite imagery. This enables the model to
associate local scene details with satellite observations, allowing it to interpret ground-level prompts more effectively.
By transferring detailed ground-level knowledge to broader
satellite contexts, these approaches improve land-use and
land-cover classification accuracy.
In this work, we extend the Sat2Cap approach by leveraging the LUCAS dataset, which contains nearly one million geotagged images across the European Union, alongside Sentinel-2 medium-resolution imagery. Our key contributions are:
1) Alignment of Sentinel-2 representations with groundlevel images. We advance zero-shot LULC classification
by directly aligning Sentinel-2 imagery with co-located
ground-level images from LUCAS, which allows the model
to understand the satellite imagery via textual descriptions associated with ground-level concepts, as done in
Sat2Cap [4]. This is done without relying on labels or
captions, in contrast to competing approaches [22, 42, 45].
Unlike in Sat2Cap [4], which focuses on higher-resolution
satellite images, our approach bridges the visual representation gap between ground-level perspectives and Sentinel-2’s
medium-resolution (10 m) multi-spectral data. This is particularly valuable given Sentinel-2’s widespread use in environmental and agricultural applications, where capturing
fine-grained details remains a challenge.
2) New state-of-the-art in zero-shot LULC classification. By coupling our SenCLIP model with a rich, LLMgenerated, set of class-specific prompts, we obtain substantial improvements in terms of zero-shot LULC classification performance on both EuroSAT and BigEarthNet, validating the usefulness of the approach for real-world zeroshot LULC mapping. Additionally, we introduce a simple prompt selection method, aiming to optimise performance by identifying the most representative prompts for
each class to enhance classification performance.
2. Related work
Zero-shot land use and land cover mapping: The largescale study of LULC with spaceborne sensors [30] has taken
large strides in terms of performance thanks to the application of deep learning-based methods [50]. Although determining some aspects of land cover, such as detecting
water, evergreen forests, or built-up areas, is often done
at an operational level at large scales [3, 8], many aspects
of land use are hard to solve employing a satellite perspective only and require the use of ground-level information [38]. This is even more so the case in a zero-shot
setting, when no class labels are available during training [43]. Indeed, the majority of previous work on zeroshot classification in remote sensing focuses on aerial or
very high resolution (<1 m) satellite imagery, where minute
details can be interpreted by humans or pretrained computer vision models [16, 19, 20, 39], with most methods
for medium resolution satellite imagery (≈ 10 m) focusing
on the more relaxed few-shot setting, where a few training
samples are available [32,33]. In this paper, we leverage the
fine-grained, easily detectable, details in geotagged groundlevel images to enable zero-shot LULC classification using
medium resolution satellite imagery.
Prompt tuning: Manual prompt engineering for zero-shot
tasks with VLMs often prioritises linguistic nuances over
visual cues, potentially limiting accuracy. To address this,
large language models (LLMs) are increasingly used to
improve prompting methods for better accuracy and robustness [24, 28]. Context Optimisation (CoOp) methods [46, 47] take a different route by learning non-textual
prompts from training data, although they struggle with
fine-grained tasks [44]. Recent approaches, like incorpo2
rating visual cues into prompts [44], or adding noise to
enhance robustness [31], have also improved VLM performance. In our work, we adapt standard, LLM-based,
and ground-level perspective prompting for remote sensing
and close the visual representation gap through cross-view
learning with geotagged images.
Cross-view learning: Geo-localised ground-level photos
offer a promising avenue to leverage the descriptive capabilities of ground-level vision models, often surpassing those
using remote sensing data. Cross-view methodologies provide insights into image similarity, localization, and orientation [21, 35, 36]. VIGOR [49] employs contrastive learning
to compare features between aerial- and street-view images,
enhancing scene analysis from diverse viewpoints. Similarly, TransGeo [48] uses attention-guided non-uniform
cropping to enrich aerial-view features with ground-level
details. However, bridging the gap between ground-level
and satellite features remains challenging, particularly with
low-resolution data. To address this, Sat2Cap [4] introduces
a cross-view modeling framework that predicts CLIP embeddings for ground-level scenes using overhead imagery.
Sat2Cap focuses on retrieval tasks and does not address the
challenges of LULC classification or the handling of lowerresolution satellite images. Our work extends the Sat2Cap
approach by targeting medium-resolution Sentinel-2 imagery and rural LULC tasks, achieving higher precision.
While Sat2Cap captures satellite image features effectively,
we enhance this by integrating four directional ground-level
images per location from the LUCAS dataset. This crossview integration enriches semantic context, leading to more
accurate Sentinel-2 image representations and a better understanding of both ground and overhead modalities.
3. Method
Our method makes use of the rich and text-aligned representation provided by CLIP [29] on ground-level images
and transfers them to a satellite image representation via
geotagged photos, similarly to [4]. As shown in Fig. 1,
we use two separate CLIP image encoders: one is kept
frozen and provides frozen ground-level embeddings, while
the other is fine-tuned for satellite data. The ground-level
embeddings serve as targets, guiding the satellite image embedding to learn the semantic space that enables the alignment of satellite-derived data with the manifold of original
CLIP embeddings from the ground-level perspective.
3.1. Self-supervised training dataset
The ground-level images used in this study were obtained from the LUCAS dataset [6], a comprehensive rural survey dataset providing Land Use and Land Cover information across Europe. The 2018 LUCAS survey consists of approximately 235,000 geotagged locations. Each
location is associated with four directional images (taken
from the north, east, west, and south), resulting in a total
of around 900,000 images. This large-scale dataset offers a
rich source of information for analyzing land use and cover
patterns.
Using the LUCAS geolocations, we accessed Sentinel2 data via the Planetary Computer API [37]. Our data retrieval focused on acquiring imagery from specific months
and years corresponding to the LUCAS dataset. To ensure
data quality, we applied a cloud coverage filter, selecting
images with less than 10-20% cloud cover. The obtained
Sentinel-2 data included RGB bands with a resolution of 10
meters per pixel and scene dimensions of 100 × 100 pixels. More details on the dataset and its distribution across
Europe are provided in supplementary.
3.2. Ground-level representation of satellite images
For the two CLIP image encoders (frozen and trainable), pairs of ground-level images (Y) and geolocated satellite images (x) are utilised, denoted as
{(Y1, x1),(Y2, x2), . . . ,(YN , xN )}. Here, Yi =
{yi,1, yi,2, . . . , yi,K} represents the set of ground-level images corresponding to the i
th location.
The frozen embeddings are obtained from ground-level
images using the pre-trained CLIP encoder, denoted as fG,
such that ground-level image embeddings are computed as:
gi,k = fG(yi,k). Simultaneously, the satellite image encoder fS is initialised with the original CLIP image encoder
and undergoes fine-tuning with Sentinel data. This results in
our fine-tuned models, which we refer to as SenCLIP when
combined with the projection head defined below.
Pooling For each location, the frozen embeddings correspond to a set of ground-level images. To consolidate these
into a single embedding Gi per location, represented by a
set of quadruplet embeddings {gi,1, gi,2, . . . , gi,K}, we explore two different pooling methods: average and attention
pooling. Average pooling (AvgPool) is a simple and efficient approach that assigns equal importance to all four directional images. The embedding Gi
is defined as follows:
Gi =
1
K
X
K
k=1
(gi,k). (1)
Attention pooling (AttPool) allows the model to focus
on the most informative features from each location. The
embedding Gi
is obtained as follows:
Gi =
X
K
k=1
(wi,k · gi,k), (2)
where wi,k(gi,k) represents the trainable attention weight
for the i-th location and the k-th image, parameterised using
a fully connected neural network.
Projection head The projection head H, adapted from the
implementation in [34], transforms the embeddings into a
3
Figure 1. Architecture: The figure illustrates the three-step pipeline consisting of Pre-Training, Prompt Selection, and Zero-shot Predictions. It also demonstrates the prompt generation process from LLMs, which is utilised for prompt selection and then selected prompts for
zero-shot prediction.
new space to capture richer relationships. It consists of
a two-layer linear neural network, with GELU activation,
dropout regularisation, and layer normalisation.
A residual connection is created by adding the output of
the first linear layer to the output of the dropout layer. The
projection head is trained alongside the rest of the model.
When combined with the trainable CLIP image encoder, the
final model produces an embedding s for the satellite image
x, as shown below:
si = SenCLIP(xi) = H(fS(xi)). (3)
Training During training, two components are trained: the
image encoder and a projection head for satellite images.
Additionally, a pooling head is incorporated into the frozen
encoder to consolidate ground-level quadruplets. The training process uses a dictionary implemented as a queue, inspired by the MoCo framework [10], to manage pooled
frozen ground-level embeddings. This mechanism allows
the reuse of encoded keys from previous iterations, with
samples gradually replaced and the oldest batch removed to
maintain consistency with newer samples. The training objective is to optimize the InfoNCE (Information Noise Contrastive Estimation) [26] contrastive loss function between
the pooled embeddings Gi from ground-level quadruplets
and the fine-tuned satellite embeddings si
. This loss function evaluates both the similarity and dissimilarity between
these two sets of embeddings, offering valuable insights
into the effectiveness of the model’s training process.
LInfoNCE = −
1
N
X
N
i=1
log
exp(Gi
· si/τ )
PN
j=1 exp(Gi
· sj/τ ))!
(4)
where τ is the temperature and N, the number of samples.
3.3. Prompting and zero-shot inference
Class-specific view-dependent prompts. We used an
LLM to generate view-specific prompts encompassing
aerial/overhead and ground-level views, as depicted in
Fig.1. Examples of generated prompts shown in supplementary. Based on the training described above, we expect SenCLIP to perform well on prompts describing LULC
classes from a ground-level perspective. We generated a
fixed number of prompts, T, for each class c ∈ [1, . . . , C].
Prompt-based zero-shot classification. The generated
prompts, represented as vectors ac,t, each prompt can be
considered to be an attribute of its corresponding class c.
The similarity between a satellite image embedding si and
the full set of text embeddings is determined through a dot
product. In order to obtain the class scores, we employ
Direct Attribute Prediction (DAP) [15]. The similarity between si and each attribute vector ac,t, calculated as si
·ac,t,
serves as a proxy for p(ac,t|si) i.e. probability of class at4
tribute given the satellite image embedding. The final classification assignment is then computed as
ci = arg max
c
Y
T
t=1
p(ac,t|si)
p(ac,t)
, (5)
where p(ac,t) is empirically estimated as the mean similarity of ac,t with the full image set.
Prompt selection method. This process involves computing a goodness score for each prompt ac,t, based on its similarity to the rest of the prompts. These scores are then used
to identify the top prompts for each class.
Specifically, we use a weighted mean score to measure
how well each prompt represents its corresponding class.
Prompts that are more representative of their class characteristics are assigned higher weighted scores. This is
achieved by calculating the mean within class similarity
αc,t =
PT
q=1 ac,t · ac,q
T
(6)
for each class, and comparing it to the overall mean similarity scores
βc,t =
PC
d=1
PT
q=1 ac,t · ad,q
C · T
. (7)
The ratio wc,t =
αc,t
βc,t
effectively evaluates the representativeness of each prompt, emphasizing those with higher
relevance to specific class characteristics. Higher weighted
scores indicate prompts that more effectively encapsulate
the essence of their class, serving as strong indicators of
class-specific attributes. This approach aligns with the objective of prioritizing prompts that are more indicative and
representative of their classes, while diminishing the influence of less relevant prompts.
4. Experiments and results
This section outlines the training implementation and hyperparameters, followed by the quantitative and qualitative
results for SenCLIP. Quantitative results cover zero-shot inference, the impact of prompt selection, and performance
improvements with LaFTer [24]. Qualitative analysis using
image captioning and cross-view image retrieval highlights
the quality of the learned representations.
4.1. Implementation details
We fine-tuned SenCLIP using two backbone CLIP encoders: ResNet50 (RN50) and ViT-B/32. The fine-tuning
strategy varied based on the model architecture: for RN50,
all layers were fine-tuned, whereas for ViT-B/32, we finetuned only the last transformer block, linear layer, and the
projection head. The AdamW optimizer, proposed by [23],
Model Arch Prompt Templates/Models Generic Aerial Ground
EuroSAT
RN50
CLIP 40.55 47.64 32.28
RemoteCLIP 25.20 29.95 22.13
SenCLIP-AvgPool 53.89 57.54 56.71
SenCLIP-AttPool 56.53 57.78 57.95
ViT-B/32
CLIP 47.26 54.87 51.66
RemoteCLIP 44.74 48.95 43.21
SkyCLIP50 55.66 66.04 59.98
GeoRSCLIP 63.40 68.02 65.82
SenCLIP-AvgPool 61.18 71.22 65.54
SenCLIP-AttPool 62.24 70.78 66.91
BigEarthNet
RN50
CLIP 27.71 29.77 24.09
RemoteCLIP 23.04 33.00 20.23
SenCLIP-AvgPool 32.74 32.41 34.39
SenCLIP-AttPool 34.61 34.88 34.80
ViT-B/32
GeoRSCLIP* 41.95 37.36 32.10
CLIP 29.80 29.50 28.37
RemoteCLIP 27.17 26.87 27.76
SkyCLIP50 20.16 29.87 20.21
SenCLIP-AvgPool 34.72 36.78 37.40
SenCLIP-AttPool 33.78 35.29 37.07
Table 1. Zero-shot performance comparison on EuroSAT and
BigEarthNet using RN50 and ViT-B/32 backbones, highlighting
the effect of unified and class-specific prompt strategies. Prompts
include a generic format, ‘centered satellite photo of {class}’,
alongside various GPT-3.5-generated aerial and ground view descriptions. *Note: GeoRSCLIP, trained on BigEarthNet with
paired text, is considered supervised rather than zero-shot.
was used with initial learning rates (LR) of 10−5
for RN50
and 10−4
for ViT-B/32. Training was conducted over 20
epochs with a batch size of 32, incorporating a step scheduler with a step size of 5 and a decay multiplier of 0.95. The
temperature parameter τ was set to 0.07 to scale the similarity scores. Data augmentation techniques included resizing,
center cropping to 32 × 32, random flipping, and rotation.
For generating the prompts, we used GPT-3.5 [27] as LLM.
The models were trained on a single NVIDIA Titan X GPU.
4.2. Quantitative results
To evaluate the effectiveness of the learned representations, we utilised two well-established Sentinel-2 benchmark datasets: EuroSAT [12] and BigEarthNet [40]. EuroSAT contains images with 10 distinct, single-class land
use/cover categories. On the other hand, BigEarthNet offers a more extensive set of annotations, with 19 multilabel classes. Consequently, Top-1 accuracy was used as
the evaluation metric for EuroSAT, while mean average precision (mAP) was employed for BigEarthNet. All evaluations were performed in a zero-shot setting, where the models were not exposed to the training sets of the benchmarks.
Classification was carried out by comparing image features
with class-associated text features.
Zero-shot inference. Table 1 summarises the zero-shot
classification performance of various models using differ5
Figure 2. Effect of prompt selection strategies on model (RN50
and ViT-B/32 Backbone) performance on the EuroSAT dataset,
varying the number of used prompts. It compares our prompt selection method, which ranks prompts from the most to least descriptive prompts (labelled as Best K and Worst K) for each class,
against a random prompt selection baseline. For the random selection baseline we also show the standard deviation over 30 trials.
ent types of prompts. Models were tested with both generic
prompts (e.g., ”a centered satellite photo of class”) and
class-specific prompts tailored to aerial and ground-level
perspectives. Each class was represented by 50 prompts for
each perspective. The comparison includes baseline models
like CLIP, RemoteCLIP, SkyCLIP [42], GeoRSCLIP [45],
alongside SenCLIP employing two pooling techniques:
AvgPool and AttPool. SenCLIP consistently outperforms
all other models, demonstrating its superior ability to leverage both aerial and ground-view prompts for enhanced classification accuracy on both dataset with both the aerial and
ground-level prompts. Specifically, for the ViT-B/32 architecture, SenCLIP improves classification performance by
over 10% for aerial prompts and ground-view prompts compared to CLIP and RemoteCLIP. While GeoRSCLIP performs competitively with generic satellite prompts, similar
to those it has been trained on, its performance declines
with more descriptive prompts. It achieves a notable accuracy on the BigEarthNet dataset. However, GeoRSCLIP
is trained on BigEarthNet with captions, making it a supervised model rather than zero-shot, limiting its comparability to other models in this context. This is also reflected in
Model/Prompts EuroSAT BigEarthNet
Aerial Ground Aerial Ground
CLIP 59.88 ± 6.08 48.33 ± 5.79 29.69 ± 5.47 29.17 ± 0.93
SenCLIP AvgPool 77.90 ± 1.22 72.87 ± 1.12 34.67 ± 0.71 44.55 ± 1.52
SenCLIP AttPool 73.58 ± 0.92 75.92 ± 2.13 34.20 ± 1.81 42.79 ± 4.14
Table 2. EuroSAT evaluation with LaFTer on top of CLIP and
SenCLIP with ViT-B/32 backbone. LaFTer text classifier is trained
for 400 epochs and fine-tuned for 20 and 5 epochs for CLIP and
SenCLIP, respectively. We used aerial and ground-level prompts.
Results are averaged over different seeds.
the fact that GeoRSCLIP underperforms SenCLIP by 5% in
BigEarthNet when using ground-level prompts, which are
further away from the generic ones used to train it. The
class-specific ground-view prompts, along with the unified
aerial prompts, showcases the SenCLIP’s ability to capture
relevant visual and semantic information, leading to superior performance compared to CLIP and remote sensing
VLMs.
Prompt selection and zero-shot. Fig. 2 illustrates the impact of prompt selection strategies on model performance
on the EuroSAT dataset with RN50 and ViT backbones.
Particularly for ViT, the best results are obtained with our
approach by selecting a few (2 or 5) prompts. For the
RN50 backbone, prompt selection with CLIP and RemoteCLIP exhibit similar results to random prompt selection due
to their lower effectiveness with ground-level prompts, resulting in varying performance between good and random
prompts. The worst K-prompt selection, with worse-thanrandom performance when few prompts are selected, highlights the efficacy of the proposed prompt selection strategy.
Zero-shot classifier tuning (LaFTer [24]) on top of SenCLIP. Table 2 presents the integration of LaFTer with CLIP
and SenCLIP models, revealing the influence of text classifier training on performance. The text classifier trained for
the LaFTer default setting of 400 epochs. SenCLIP demonstrates superior performance when employing ground-view
and aerial-view prompts (50 per class), for both EuroSAT
and BigEarthNet. We found that SenCLIP achieves high
level performance with fine-tuning for up to 5 epochs, while
CLIP requires 20 epochs to achieve the best results without over-fitting. This could be attributed to SenCLIP being optimised specifically for remote sensing tasks, whereas
CLIP has more generalised embeddings that require additional training to optimise.
4.3. Qualitative results on cross-modal retrieval
Qualitative analysis of SenCLIP embeddings using ClipCap [25] To further analyse the embeddings learned by
SenCLIP, we conducted a qualitative analysis using the
ClipCap image caption generator [25]. As shown in Fig.
3, the captions generated by SenCLIP provide detailed descriptions of the ground-level view. In contrast, captions
6
Figure 3. Image captioning on EuroSAT images using ClipCap [25]
produced by CLIP and RemoteCLIP predominantly reflect
an aerial perspective, often including terms such as “aerial
view”, “photo of” and referencing perspectives from aircraft, video, and camera angles. This distinction underscores SenCLIP’s superior ability to capture ground-level
details, offering a more nuanced understanding of the scene
compared to its counterparts.
Image-to-image retrieval - satellite to ground-level. We
conducted an image-to-image retrieval experiment to identify ground-level images corresponding to a given satellite
image. As depicted in Fig. 4a, we leveraged EuroSAT images from different classes to identify the two nearest neighbor ground-level LUCAS images. The results demonstrate
SenCLIP’s strong ability to accurately retrieve ground-level
images that align with the given class, significantly outperforming CLIP and RemoteCLIP. The latter models struggled across several classes and frequently selected outlier LUCAS images, highlighting their limitations in establishing robust mappings between satellite and ground-level
views. Notably, SenCLIP’s fine-grained feature alignment
is especially apparent in the annual crops class, where the
retrieved ground-level images showcase detailed views of
plantations.
Image-to-image retrieval - ground-level to satellite. In
our exploration of image-to-image retrieval, we investigated
the process of mapping LUCAS ground-level images to EuroSAT satellite images, as shown in Fig. 4b. For this analysis, we used the top-2 LUCAS images given an example
from EuroSAT, as depicted in Fig. 4a. The results demonstrate that SenCLIP excels in accurately identifying the correct classes in the majority of cases. However, it is worth
noting that CLIP and RemoteCLIP perform better in this
scenario than in EuroSAT to LUCAS.
5. Conclusion
This study highlights the benefits of cross-view finetuning of CLIP, enabling a remote sensing model to
effectively capture ground-level semantic details using
medium-resolution Sentinel-2 images. Unlike conventional
models, which often struggle with domain-specific terms
and predefined class names, our approach demonstrates
remarkable flexibility in accommodating diverse prompting
styles for zero-shot LULC classification. This flexibility
paves the way for the creation of custom LULC maps
without requiring any additional training data. The
model’s success can be attributed to its comprehensive
self-supervised training, which aligns Sentinel-2 representations with CLIP representations of co-located, geotagged,
ground-level images from the European Union-wide
LUCAS dataset. Furthermore, we introduce an efficient
prompt selection method, highlighting the importance of
prompt curation. Overall, this work combines cross-view
7
(a) EuroSAT to LUCAS
(b) LUCAS To EuroSAT
Figure 4. Qualitative image-to-image retrieval: This analysis demonstrates the qualitative effectiveness of SenCLIP embeddings in both
directions. By identifying the top-2 nearest LUCAS embeddings from EuroSAT images, the results indicate that the model successfully
learns the fine-grained relationships between ground-level and satellite imagery. Conversely, using ground-level LUCAS images to find
the top-2 nearest neighbor satellite images from EuroSAT, the analysis further demonstrates the model’s capability to map embeddings
bidirectionally, effectively capturing and relating fine-grained details between the two image domains.
training and prompt selection to empower models like
SenCLIP, enabling them to surpass the limitations of
traditional remote sensing methods. By incorporating
ground-level landscape descriptions, SenCLIP sets a new
benchmark for zero-shot LULC mapping.
Acknowledgements
This research was supported by the ‘Giving Rural Actors
8
Novel Data and Re-Usable Tools to Lead Public Action in
Rural Areas’ (GRANULAR) project, which has received
funding from the European Union’s Horizon Europe Research and Innovation Programme under Grant Agreement
No. 101061068.
References
[1] James Urquhart Allingham, Jie Ren, Michael W Dusenberry,
Xiuye Gu, Yin Cui, Dustin Tran, Jeremiah Zhe Liu, and Balaji Lakshminarayanan. A simple zero-shot prompt weighting technique to improve prompt ensembling in text-image
models. In International Conference on Machine Learning,
pages 547–568. PMLR, 2023. 2
[2] James Richard Anderson. A land use and land cover classification system for use with remote sensor data, volume 964.
US Government Printing Office, 1976. 1
[3] Gyorgy B ¨ uttner. Corine land cover and land cover change ¨
products. In Land use and land cover mapping in Europe:
practices & trends, pages 55–74. Springer, 2014. 2
[4] Aayush Dhakal, Adeel Ahmad, Subash Khanal, Srikumar
Sastry, and Nathan Jacobs. Sat2cap: Mapping fine-grained
textual descriptions from satellite images. arXiv preprint
arXiv:2307.15904, 2023. 2, 3
[5] Claude E Duchon. Lanczos filtering in one and two dimensions. Journal of Applied Meteorology and Climatology,
18(8):1016–1022, 1979. 11
[6] Raphael d’Andrimont, Momchil Yordanov, Laura Martinez- ¨
Sanchez, Beatrice Eiselt, Alessandra Palmieri, Paolo Dominici, Javier Gallego, Hannes Isaak Reuter, Christian Joebges, Guido Lemoine, et al. Harmonised lucas in-situ land
cover and use database for field surveys from 2006 to 2018
in the european union. Scientific data, 7(1):352, 2020. 3, 11
[7] Gregory Giuliani, Paolo Mazzetti, Mattia Santoro, Stefano
Nativi, Joost Van Bemmelen, Guido Colangeli, and Anthony
Lehmann. Knowledge generation using satellite earth observations to support sustainable development goals (sdg):
A use case on land degradation. International Journal of
Applied Earth Observation and Geoinformation, 88:102068,
2020. 1
[8] Matthew C Hansen, Peter V Potapov, Rebecca Moore, Matt
Hancher, Svetlana A Turubanova, Alexandra Tyukavina,
David Thau, Stephen V Stehman, Scott J Goetz, Thomas R
Loveland, et al. High-resolution global maps of 21st-century
forest cover change. science, 342(6160):850–853, 2013. 2
[9] Peter K. Hargreaves and Gary R. Watmough. Satellite earth
observation to support sustainable rural development. International Journal of Applied Earth Observation and Geoinformation, 103:102466, 2021. 1
[10] Kaiming He, Haoqi Fan, Yuxin Wu, Saining Xie, and Ross
Girshick. Momentum contrast for unsupervised visual representation learning. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages
9729–9738, 2020. 4
[11] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun.
Deep residual learning for image recognition. In Proceedings of the IEEE conference on computer vision and pattern
recognition, pages 770–778, 2016. 1
[12] Patrick Helber, Benjamin Bischke, Andreas Dengel, and
Damian Borth. Eurosat: A novel dataset and deep learning
benchmark for land use and land cover classification. IEEE
Journal of Selected Topics in Applied Earth Observations
and Remote Sensing, 12(7):2217–2226, 2019. 5
[13] Chao Jia, Yinfei Yang, Ye Xia, Yi-Ting Chen, Zarana Parekh,
Hieu Pham, Quoc Le, Yun-Hsuan Sung, Zhen Li, and Tom
Duerig. Scaling up visual and vision-language representation learning with noisy text supervision. In International
conference on machine learning, pages 4904–4916. PMLR,
2021. 1
[14] Alex Krizhevsky, Ilya Sutskever, and Geoffrey E Hinton.
Imagenet classification with deep convolutional neural networks. Advances in neural information processing systems,
25, 2012. 1
[15] Christoph H Lampert, Hannes Nickisch, and Stefan Harmeling. Learning to detect unseen object classes by betweenclass attribute transfer. In 2009 IEEE conference on computer vision and pattern recognition, pages 951–958. IEEE,
2009. 4
[16] Aoxue Li, Zhiwu Lu, Liwei Wang, Tao Xiang, and Ji-Rong
Wen. Zero-shot scene classification for high spatial resolution remote sensing images. IEEE Transactions on Geoscience and Remote Sensing, 55(7):4157–4167, 2017. 2
[17] Junnan Li, Dongxu Li, Silvio Savarese, and Steven Hoi.
Blip-2: Bootstrapping language-image pre-training with
frozen image encoders and large language models. arXiv
preprint arXiv:2301.12597, 2023. 1
[18] Junnan Li, Dongxu Li, Caiming Xiong, and Steven Hoi.
Blip: Bootstrapping language-image pre-training for unified vision-language understanding and generation. In International Conference on Machine Learning, pages 12888–
12900. PMLR, 2022. 1
[19] Xiang Li, Congcong Wen, Yuan Hu, and Nan Zhou. Rs-clip:
Zero shot remote sensing scene classification via contrastive
vision-language supervision. International Journal of Applied Earth Observation and Geoinformation, 124:103497,
2023. 2
[20] Yansheng Li, Deyu Kong, Yongjun Zhang, Yihua Tan, and
Ling Chen. Robust deep alignment network with remote
sensing knowledge graph for zero-shot and generalized zeroshot remote sensing image scene classification. ISPRS Journal of Photogrammetry and Remote Sensing, 179:145–158,
2021. 2
[21] Tsung-Yi Lin, Yin Cui, Serge Belongie, and James Hays.
Learning deep representations for ground-to-aerial geolocalization. In Proceedings of the IEEE conference on computer
vision and pattern recognition, pages 5007–5015, 2015. 3
[22] Fan Liu, Delong Chen, Zhangqingyun Guan, Xiaocong
Zhou, Jiale Zhu, and Jun Zhou. Remoteclip: A vision language foundation model for remote sensing. arXiv preprint
arXiv:2306.11029, 2023. 2, 12
[23] Ilya Loshchilov and Frank Hutter. Decoupled weight decay
regularization. arXiv preprint arXiv:1711.05101, 2017. 5
[24] M. Jehanzeb Mirza, Leonid Karlinsky, Wei Lin, Mateusz Kozinski, Horst Possegger, Rogerio Feris, and Horst
Bischof. Lafter: Label-free tuning of zero-shot classifier using language and unlabeled image collections. In Conference
9
on Neural Information Processing Systems (NeurIPS), 2023.
2, 5, 6
[25] Ron Mokady, Amir Hertz, and Amit H Bermano. Clipcap: Clip prefix for image captioning. arXiv preprint
arXiv:2111.09734, 2021. 6, 7
[26] Aaron van den Oord, Yazhe Li, and Oriol Vinyals. Representation learning with contrastive predictive coding. arXiv
preprint arXiv:1807.03748, 2018. 4
[27] Long Ouyang, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll Wainwright, Pamela Mishkin, Chong Zhang, Sandhini
Agarwal, Katarina Slama, Alex Ray, et al. Training language
models to follow instructions with human feedback. Advances in neural information processing systems, 35:27730–
27744, 2022. 5, 12
[28] Sarah Pratt, Ian Covert, Rosanne Liu, and Ali Farhadi. What
does a platypus look like? generating customized prompts
for zero-shot image classification. In Proceedings of the
IEEE/CVF International Conference on Computer Vision,
pages 15691–15701, 2023. 2
[29] Alec Radford, Jong Wook Kim, Chris Hallacy, Aditya
Ramesh, Gabriel Goh, Sandhini Agarwal, Girish Sastry,
Amanda Askell, Pamela Mishkin, Jack Clark, et al. Learning
transferable visual models from natural language supervision. In International conference on machine learning, pages
8748–8763. PMLR, 2021. 1, 2, 3, 12
[30] John Rogan and DongMei Chen. Remote sensing technology
for mapping and monitoring land-cover and land-use change.
Progress in planning, 61(4):301–325, 2004. 2
[31] Karsten Roth, Jae Myung Kim, A Koepke, Oriol Vinyals,
Cordelia Schmid, and Zeynep Akata. Waffling around for
performance: Visual classification with random words and
broad concepts. arXiv preprint arXiv:2306.07282, 2023. 2,
3
[32] Marc Rußwurm, Sherrie Wang, Marco Korner, and David
Lobell. Meta-learning for few-shot land cover classification.
In Proceedings of the ieee/cvf conference on computer vision
and pattern recognition workshops, pages 200–201, 2020. 2
[33] Marc Rußwurm, Sherrie Wang, and Devis Tuia. Humans
are poor few-shot classifiers for sentinel-2 land cover. In
IGARSS 2022-2022 IEEE International Geoscience and Remote Sensing Symposium, pages 4859–4862. IEEE, 2022. 2
[34] M. Moein Shariatnia. Simple CLIP, 4 2021. 3
[35] Yujiao Shi and Hongdong Li. Beyond cross-view image
retrieval: Highly accurate vehicle localization using satellite image. In Proceedings of the IEEE/CVF Conference
on Computer Vision and Pattern Recognition, pages 17010–
17020, 2022. 3
[36] Yujiao Shi, Xin Yu, Dylan Campbell, and Hongdong Li.
Where am i looking at? joint location and orientation estimation by cross-view matching. In Proceedings of the
IEEE/CVF Conference on Computer Vision and Pattern
Recognition, pages 4064–4072, 2020. 3
[37] Microsoft Open Source, Matt McFarland, Rob
Emanuele, Dan Morris, and Tom Augspurger. microsoft/planetarycomputer: October 2022, oct 2022. 3
[38] Shivangi Srivastava, John E Vargas Munoz, Sylvain Lobry,
and Devis Tuia. Fine-grained landuse characterization using ground-based pictures: a deep learning solution based on
globally available data. International Journal of Geographical Information Science, 34(6):1117–1136, 2020. 2
[39] Gencer Sumbul, Ramazan Gokberk Cinbis, and Selim Aksoy. Fine-grained object recognition and zero-shot learning in remote sensing imagery. IEEE Transactions on Geoscience and Remote Sensing, 56(2):770–779, 2017. 2
[40] Gencer Sumbul, Jian Kang, Tristan Kreuziger, Filipe
Marcelino, Hugo Costa, Pedro Benevides, Mario Caetano, and Begum Demir. Bigearthnet dataset with a new ¨
class-nomenclature for remote sensing image understanding.
arXiv preprint arXiv:2001.06372, 2020. 5
[41] Billie L Turner, Eric F Lambin, and Anette Reenberg. The
emergence of land change science for global environmental change and sustainability. Proceedings of the National
Academy of Sciences, 104(52):20666–20671, 2007. 1
[42] Zhecheng Wang, Rajanie Prabha, Tianyuan Huang, Jiajun
Wu, and Ram Rajagopal. Skyscript: A large and semantically diverse vision-language dataset for remote sensing.
In Proceedings of the AAAI Conference on Artificial Intelligence, volume 38, pages 5805–5813, 2024. 2, 6, 12
[43] Meiliu Wu, Qunying Huang, Song Gao, and Zhou Zhang.
Mixed land use measurement and mapping with street view
images and spatial context-aware prompts via zero-shot multimodal learning. International Journal of Applied Earth Observation and Geoinformation, 125:103591, 2023. 2
[44] Yi Zhang, Ce Zhang, Ke Yu, Yushun Tang, and Zhihai He.
Concept-guided prompt learning for generalization in visionlanguage models. arXiv preprint arXiv:2401.07457, 2024. 2,
3
[45] Zilun Zhang, Tiancheng Zhao, Yulong Guo, and Jianwei
Yin. Rs5m: A large scale vision-language dataset for remote
sensing vision-language foundation model. arXiv preprint
arXiv:2306.11300, 2023. 2, 6, 12
[46] Kaiyang Zhou, Jingkang Yang, Chen Change Loy, and Ziwei
Liu. Conditional prompt learning for vision-language models. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 16816–16825,
2022. 2
[47] Kaiyang Zhou, Jingkang Yang, Chen Change Loy, and Ziwei
Liu. Learning to prompt for vision-language models. International Journal of Computer Vision, 130(9):2337–2348,
2022. 1, 2
[48] Sijie Zhu, Mubarak Shah, and Chen Chen. Transgeo: Transformer is all you need for cross-view image geo-localization.
In Proceedings of the IEEE/CVF Conference on Computer
Vision and Pattern Recognition, pages 1162–1171, 2022. 3
[49] Sijie Zhu, Taojiannan Yang, and Chen Chen. Vigor: Crossview image geo-localization beyond one-to-one retrieval. In
Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pages 3640–3649, 2021. 3
[50] Xiao Xiang Zhu, Devis Tuia, Lichao Mou, Gui-Song Xia,
Liangpei Zhang, Feng Xu, and Friedrich Fraundorfer. Deep
learning in remote sensing: A comprehensive review and list
of resources. IEEE geoscience and remote sensing magazine,
5(4):8–36, 2017. 1, 2
10
A. Appendices
A.1. Dataset Overview
The LUCAS dataset [6], encompassing data from 2006,
2009, 2012, 2015, and 2018, includes high-resolution images captured at 1600×1200 pixels. For this work, we focused on the 2018 dataset and downsampled these images
to 512×512 pixels using the LANCZOS [5] interpolation
method. This technique was selected for its superior resampling quality, ensuring the preservation of image detail
and clarity. Figure A.1 illustrates the geographical distribution of geo-tags across Europe, while Figure A.3 showcases
examples of the four directional LUCAS images alongside
their corresponding Sentinel-2 images obtained from the
Planetary API.
A.2. Meta Prompts and Prompt Example
In this work, we generated ground and aerial prompts
using the meta-prompt approach described in “Meta Prompt
for Ground View Prompts”, and further refined them based
on different views, such as “aerial” shown in “Meta Prompt
for Aerial View Prompts”, as well as prompt length. An
example of the generated prompts for the “Forest” class is
shown in Fig A.2.
Figure A.1. Data Distribution across Europe
Meta Prompt for Ground View Prompts
Generate 50 extremely short and diverse sentences
that may correspond to factual visual descriptions
of photos taken over the land-use/land-cover class
‘Annual Crop’ such that they are as different as possible from all of these other classes:
[‘Industrial’, ‘Pasture’, ‘River’, ‘Forest’, ‘Herbaceous Vegetation’, ‘Permanent Crop’, ‘Highway’,
‘Residential’, ‘Sea Lake’]
Try to describe visual features or objects that are
likely to be visible in such images, even if they are
not stereotypical. Make sure they cover as many of
all the possible random photos that could be taken
over that land-use/land-cover and that they sound
as objective as possible, covering different seasons
and states of the land-use/land-cover. Make sure to
add some examples related to the class for the image
visual description. Do not make poetic sentences
but more factual.
Meta Prompt for Aerial View Prompts
Generate 50 extremely short and diverse sentences
that may correspond to factual visual descriptions of
aerial or satellite view over the land-use/land-cover
class ‘Annual Crop’ such that there are as different
as possible from all of these other classes:
[‘Annual Crop’, ‘Industrial’, ‘Pasture’, ‘River’,
‘Forest’, ‘Herbaceous Vegetation’, ‘Permanent
Crop’, ‘Highway’, ‘Residential’, ‘Sea Lake’]
Try to describe aerial or satellite visual features
or objects that are likely to be visible in such images, even if they are not stereotypical. Add aerial
view context with patterns and use ”aerial”, ”satellite photo” terms. Make sure they cover as many of
all the possible random photos that could be taken
over that land-use/land-cover and that they sound
as objective as possible, covering different seasons
and states of the land-use/land-cover. Make sure to
add some examples related to the class for the image aerial or satellite visual attributes. Do not make
poetic sentences but more factual.
A.3. Zeroshot Results based on Length of Prompts
In addition to generating prompts from aerial and ground
perspectives, we further diversified the prompt styles by incorporating varying lengths: short sentences (10 words) and
long sentences (50 words), tailored to the specific class under consideration, as illustrated in Fig A.2. Table A.1 reveals several key insights regarding the impact of prompt
length and view-type on zero-shot classification perfor11
Figure A.2. Examples of different style prompts generated for ”Forest” class by GPT3.5 [27]
Prompt Templates/Models Aerial Short Aerial Long Ground Short Ground Long
EuroSAT
RN50
CLIP [29] 31.95 38.42 28.56 31.32
RemoteCLIP [22] 24.82 27.80 23.84 20.90
SenCLIP-AvgPool 57.74 57.02 59.10 55.46
SenCLIP-AttPool 58.68 56.34 60.12 55.92
ViT-B/32
CLIP [29] 45.09 49.61 40.97 41.76
RemoteCLIP [22] 37.94 38.85 37.54 35.30
SkyCLIP [42] 61.05 59.20 53.25 54.03
GeoRSCLIP [45] 62.46 62.91 60.00 57.88
SenCLIP-AvgPool 63.78 66.89 64.28 58.80
SenCLIP-AttPool 64.10 67.54 63.04 57.82
BigEarthNet
RN50
CLIP [29] 27.60 30.02 24.41 23.78
RemoteCLIP [22] 32.60 32.14 31.74 30.66
SenCLIP-AvgPool 33.57 33.60 30.02 32.70
SenCLIP-AttPool 35.18 35.89 32.74 35.09
ViT-B/32
CLIP [29] 28.58 34.12 27.51 28.94
RemoteCLIP [22] 32.75 28.38 29.97 25.44
SkyCLIP [42] 25.77 28.08 23.43 21.55
GeoRSCLIP* [45] 37.24 39.05 30.95 33.75
SenCLIP-AvgPool 33.08 35.66 34.36 34.57
SenCLIP-AttPool 33.67 33.76 33.80 33.95
Table A.1. Zero-shot classification results with RN50 and ViTB/32 backbones on EuroSAT and BigEarthNet datasets, highlighting the effectiveness of various prompt lengths and types. The
comparison includes specific class prompts with short (10-word)
and long (50-word) sentence descriptions for aerial and ground
views, all generated using GPT-3.5. *Note: GeoRSCLIP [45],
trained on BigEarthNet with paired text, is considered supervised
rather than zero-shot. Bold indicates the each model’s performance on short versus long prompts, while italic highlights the
overall best-performing model across short and long.
mance.
Effect of Prompt Length: Across both the EuroSAT and
BigEarthNet datasets, longer prompts (50 words) generally outperform shorter ones (10 words), particularly for
aerial views. This trend holds across all models, which
show improved accuracy when provided with more detailed
prompts. For instance, SenCLIP exhibits notable accuracy
improvements with longer prompts on both datasets, especially in aerial views, with the exception of RN50 on EuroSAT.
Ground Views and Prompt Length: In contrast to aerial
views, the effect of prompt length is less pronounced for
ground-level images. Models like RemoteCLIP [22] and
SenCLIP often perform equally well or slightly better with
shorter prompts compared to longer ones. This is likely due
to the rich visual context inherent in ground-level images,
where detailed descriptions in longer prompts may add limited value. For example, in the EuroSAT dataset, SenCLIPAvgPool and SenCLIP-AttPool show minimal gains from
longer prompts in ground views, suggesting that prompt
specificity may matter more than length for ground-level
imagery.
Moreover, SenCLIP variants consistently outperform
other models in both aerial and ground views across
both datasets, demonstrating the robustness of its crossview strategies in leveraging detailed descriptions. While
GeoRSCLIP [45], a supervised model, benefits from longer
prompts (particularly in BigEarthNet), it is consistently outperformed by SenCLIP in ground-view scenarios. For example, SenCLIP achieves significant performance gains on
ground-level imagery within the BigEarthNet dataset.
12
Figure A.3. Sentinel-2 collected images from Geo-Tagged LUCAS data points. LUCAS images include four directional views, which are
displayed alongside the Sentinel-2 imagery with 10m resolution.
13