# Resolvents

## 1. Motivation
The notion of resolvent is one of the central tools in the computation of Galois groups of polynomials. Its relevance comes from the following principle:

> Starting from a polynomial $f$, one builds auxiliary polynomials whose arithmetic behaviour reflects structural information about $\mathrm{Gal}(f)$.

In practice, a resolvent transforms information about the action of the Galois group on the roots of $f$ into information about a polynomial with coefficients in the base field. This is useful because such arithmetic information can often be checked directly: for example,

* Whether a resolvent has a rational root.
* Whether it factors over the base field.
* Whether its discriminant is a square.

These properties can force the Galois group to be contained in a specific subgroup of $S_n$, or can rule out certain possibilities.

This is why resolvents are especially important in computational Galois theory. In the degree $\le 5$ setting, they provide the bridge between:
1. The abstract permutation action on the roots.
2. Explicit arithmetic tests over $\mathbb{Q}$.

In particular, resolvents play an essential role in the computation of Galois groups of polynomials of degree at most 5.

---

## 2. The action of $S_n$ on polynomials in the roots
Let 
$$x := (x_1,\dots,x_n)$$
and let $p \in K[x_1,\dots,x_n]$. For each subgroup $G \le S_n$, define:
$$\operatorname{Stab}_G(p) := \{\sigma \in G : \widetilde{\sigma}(p)=p\},$$
and
$$O_{G,p} := \{\widetilde{\tau}(p) : \tau \in G\}.$$

Here $\widetilde{\sigma}$ denotes the natural action induced by $\sigma$ on the variables $x_1,\dots,x_n$. When $G=S_n$, we simply write
$$O_p := O_{S_n,p}.$$

Thus:
* $\operatorname{Stab}_G(p)$ is the stabilizer of $p$ under the action of $G$.
* $O_{G,p}$ is the orbit of $p$ under the action of $G$.

The subgroup $\operatorname{Stab}_G(p)$ defines a right congruence relation on $G$, and the canonical map
$$G / R_{\operatorname{Stab}_G(p)} \longrightarrow O_{G,p}, \qquad \operatorname{Stab}_G(p)\tau \longmapsto \widetilde{\tau}(p)$$
is a well-defined bijection. In particular,
$$|O_{G,p}| = [G : \operatorname{Stab}_G(p)].$$

This is the basic group-theoretic mechanism behind resolvents: the orbit size is controlled by the stabilizer. Moreover, for every $\sigma \in G$,
$$\sigma^{-1}\operatorname{Stab}_G(p)\sigma = \operatorname{Stab}_G(\widetilde{\sigma}(p)).$$
This shows that stabilizers of elements in the same orbit are conjugate.

---

## 3. Universal resolvent
Given $p \in K[x_1,\dots,x_n]$, its universal resolvent is defined by
$$R_p(t) := \prod_{q \in O_p} (t-q(x)) \in K[x_1,\dots,x_n,t].$$

This construction depends only on the orbit of $p$ under $S_n$. In fact, if $q \in O_p$, then
$$O_p = O_q, \qquad \text{hence} \qquad R_p = R_q.$$
So the universal resolvent is really attached to the orbit, not to a particular representative.

A key fact is that the coefficients of $R_p(t)$ are fixed by the action of $S_n$. Therefore they belong to the ring of symmetric polynomials, and one obtains
$$R_p(t) \in K[s_1,\dots,s_n][t],$$
where $s_1,\dots,s_n$ denote the elementary symmetric polynomials in $x_1,\dots,x_n$.

This point is fundamental: although $R_p$ is defined through the orbit of a polynomial in the variables $x_1,\dots,x_n$, its coefficients can be expressed in terms of symmetric data only.

---

## 4. Specialized resolvent
Let now $f \in K[t]$ be an irreducible polynomial of degree $n$, let $K_f$ be a splitting field of $f$ over $K$, and let
$$\alpha_1,\dots,\alpha_n \in K_f$$
be the $n$ distinct roots of $f$. Write
$$\alpha := (\alpha_1,\dots,\alpha_n), \qquad x := (x_1,\dots,x_n).$$

Consider the unique $K$-homomorphism
$$\operatorname{ev}_{\alpha} : K(x) \to K_f$$
such that
$$\operatorname{ev}_{\alpha}(x_i)=\alpha_i \qquad \text{for } 1 \le i \le n.$$

Its extension fixing the variable $t$ will also be denoted by
$$\operatorname{ev}_{\alpha} : K(x)[t] \to K_f[t].$$

If
$$f(t)=(t-\alpha_1)\cdots(t-\alpha_n) = t^n + \sum_{k=1}^{n} (-1)^k c_k t^{n-k},$$
and $g_n$ denotes the general polynomial of degree $n$, then
$$f = \operatorname{ev}_{\alpha}(g_n), \qquad c_k = \operatorname{ev}_{\alpha}(s_k).$$

Now let $p \in K[x_1,\dots,x_n]$. We write
$$p(\alpha):=\operatorname{ev}_{\alpha}(p)\in K_f.$$

For each permutation $\sigma \in G_K(f)\subseteq S_n$, the quantity $\sigma(p(\alpha))$ is well-defined in $K_f$, and one has
$$\widetilde{\sigma}(p)(\alpha)=\sigma(p(\alpha)).$$

The specialized resolvent of $p$ at $f$ is then defined as
$$R_{f,p}(t) := \prod_{q \in O_p} (t-q(\alpha)) \in K[t].$$

Equivalently,
$$R_{f,p} = \operatorname{ev}_{\alpha}(R_p).$$

This is the resolvent that is actually used in arithmetic applications: it is a polynomial over the base field $K$, obtained by specializing the universal construction at the roots of $f$.

---

## 5. Why specialized resolvents are useful in Galois theory


The crucial point is that the roots of $R_{f,p}$ are the values
$$q(\alpha), \qquad q \in O_p,$$
and these values are closely linked to the action of the Galois group on the roots of $f$.

More precisely:
* Every root $q(\alpha)$ of $R_{f,p}$ lies in the splitting field $$K_f = K(\alpha_1,\dots,\alpha_n),$$ since $q \in O_p \subset K[x_1,\dots,x_n]$.
* For every $\sigma \in S_n$, $$\operatorname{Stab}_{G_K(f)}(\widetilde{\sigma}(p)) \subseteq G\bigl(K_f : K(\widetilde{\sigma}(p)(\alpha))\bigr).$$
* If $$\sigma G_K(f) \sigma^{-1} \subseteq \operatorname{Stab}_{S_n}(p),$$then$$\widetilde{\sigma}(p)(\alpha)\in K.$$
* Conversely, if $\widetilde{\sigma}(p)(\alpha)\in K$ and is a simple root of $R_{f,p}$, then $$\sigma G_K(f) \sigma^{-1} \subseteq \operatorname{Stab}_{S_n}(p).$$

These statements explain the usefulness of resolvents:
* If the specialized resolvent has a root in the base field,
* Or more generally if it factors in a particular way,
* Then one can deduce subgroup information about the Galois group.

In other words, resolvents convert group-theoretic information into arithmetic information. This is exactly why they are so valuable in practice: instead of trying to understand the Galois group directly inside $S_n$, one studies an auxiliary polynomial defined over $K$.

---

## 6. Example: the discriminant resolvent
Consider
$$\delta(x) := \prod_{1\le i<j\le n}(x_i-x_j), \qquad \Delta(x):=\delta(x)^2.$$

For each permutation $\sigma \in S_n$, one has
$$(\widetilde{\sigma}(\delta))^2 = \Delta.$$

Hence $\widetilde{\sigma}(\delta)\in\{\delta,-\delta\}$. Since the identity fixes $\delta$ and a transposition sends $\delta$ to $-\delta$, the orbit is exactly
$$O_{\delta}=\{\delta,-\delta\}.$$

Therefore,
$$R_{\delta}(t) = \prod_{q\in O_{\delta}} (t-q(x)) = (t-\delta(x))(t+\delta(x)) = t^2-\delta(x)^2 = t^2-\Delta(x).$$

This simple example already shows the power of the method: the discriminant appears naturally as the coefficient of a resolvent.
After specialization, one obtains the classical criterion:

> For an irreducible polynomial $f \in K[t]$ of degree $n$, the Galois group $G_K(f)$ is contained in $A_n$ if and only if $\Delta(f)$ is a square in $K$.

Thus the discriminant criterion is itself an instance of the general theory of resolvents.

---

## 7. Example: the cubic resolvent for quartics
Now consider the case $n=4$, and define
$$p_1 := (x_1+x_2)(x_3+x_4).$$

To compute its resolvent, we first study its orbit. Consider the transpositions
$$\sigma_1 := (2,3), \qquad \sigma_2 := (2,4).$$

Then
$$p_2 := \widetilde{\sigma_1}(p_1) = (x_1+x_3)(x_2+x_4),$$
$$p_3 := \widetilde{\sigma_2}(p_1) = (x_1+x_4)(x_2+x_3).$$

These three polynomials are distinct, so the orbit has at least three elements. On the other hand, one checks that $\operatorname{Stab}_{S_4}(p_1)$ has order 8, and therefore
$$|O_{p_1}| = [S_4 : \operatorname{Stab}_{S_4}(p_1)] = \frac{24}{8} = 3.$$

Hence
$$O_{p_1} = \{p_1,p_2,p_3\}.$$

The universal resolvent is therefore
$$R_{p_1}(t) = \prod_{i=1}^{3}(t-p_i(x)).$$

Expanding, one obtains
$$R_{p_1}(t) = t^3 - (p_1(x)+p_2(x)+p_3(x))t^2 + (p_1(x)p_2(x)+p_1(x)p_3(x)+p_2(x)p_3(x))t - p_1(x)p_2(x)p_3(x).$$

Expressed in the elementary symmetric polynomials $s_1,s_2,s_3,s_4$, this becomes
$$R_{p_1}(t) = t^3 - 2s_2 t^2 + (s_2^2+s_1s_3-4s_4)t + (s_4s_1^2+s_3^2-s_1s_2s_3).$$

This is the classical cubic resolvent attached to a quartic. A useful fact is that the discriminants of
$$f(t)=\prod_{i=1}^{4}(t-x_i) \qquad \text{and} \qquad R_{p_1}(t)$$
coincide. Indeed,
$$\Delta(R_{p_1}) = (p_1-p_2)^2 (p_1-p_3)^2 (p_2-p_3)^2 = \Delta(f).$$

After specialization at a quartic polynomial $f$, the polynomial $R_{f,p_1}$ is precisely the cubic resolvent used in the classification of quartic Galois groups. This makes the quartic case especially important computationally: instead of working directly with the action of the Galois group on four roots, one studies a cubic polynomial over the base field.

---

## 8. Resolvents in degree $\le 5$ Galois group computations
For polynomials of small degree, resolvents provide explicit tests that sharply restrict the Galois group. Typical examples are:
* The discriminant resolvent, which detects whether the Galois group is contained in $A_n$.
* The cubic resolvent of a quartic, which helps distinguish between the possible transitive subgroups of $S_4$.
* Higher-degree resolvents in degree 5, which similarly reduce group-theoretic questions to arithmetic ones.

From the point of view of proof-carrying certificates, resolvents are particularly attractive because they isolate a concrete mathematical object:
* A polynomial over the base field.
* Canonically attached to a choice of polynomial $p$ in the roots.
* Whose arithmetic properties can be certified explicitly.

This is why resolvents are a natural component of OpenGalois: they turn structural statements about Galois groups into verifiable statements about explicitly computed polynomials.

---

## 9. Relation with ResolventQQ
In OpenGalois, the fact
$$\texttt{ResolventQQ}(R,f,p)$$
expresses exactly that $R$ is the specialized resolvent of $p$ at $f$ over $\mathbb{Q}$, i.e.
$$R = R_{f,p}.$$

The fact itself is purely mathematical. It does not encode side conditions such as the compatibility between the degree of $f$ and the number of variables of $p$; those belong to the rule that proves the fact.

Thus the general theory is separated from the computational strategy:
* Mathematically, one works with the full notion of specialized resolvent.
* Computationally, one may later certify only particular instances, such as the quartic cubic resolvent arising from
$$p_1=(x_1+x_2)(x_3+x_4).$$

---

## 10. Summary
The theory of resolvents proceeds in two steps:
1. Start with a polynomial $p$ in the variables $x_1,\dots,x_n$, and build its universal resolvent 
$$R_p(t)=\prod_{q\in O_p}(t-q(x));$$
2. Specialize at the roots of an irreducible polynomial $f$, obtaining 
$$R_{f,p}(t)=\prod_{q\in O_p}(t-q(\alpha)).$$

The importance of this construction lies in the fact that the arithmetic behaviour of $R_{f,p}$ reflects subgroup information about the Galois group of $f$. For this reason, resolvents are among the most effective and classical tools in explicit Galois theory.