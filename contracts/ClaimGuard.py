# v1.0.1
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
import json
import genlayer.gl as gl

class ClaimGuard(gl.Contract):
    CATEGORIES = [
        "prediction_market",
        "bounty_verification",
        "content_moderation",
        "identity_verification",
        "fact_check",
        "custom",
    ]

    # State variables MUST be class-level in GenLayer IC
    owner = ""
    claim_count = 0
    min_stake = 100
    claims = "{}"
    resolvers = "{}"

    @gl.public.write
    def init(self):
        self.owner = str(gl.message.sender_address)
        self.claim_count = 0
        self.min_stake = 100
        self.claims = "{}"
        self.resolvers = json.dumps({str(gl.message.sender_address): True})

    @gl.public.view
    def getOwner(self):
        return self.owner

    @gl.public.write
    def createClaim(self, evidence_url, expected_content, description, category):
        if category not in self.CATEGORIES:
            raise ValueError("Invalid category")
        self.claim_count += 1
        claims = self._load_claims()
        claims[str(self.claim_count)] = {
            "id": str(self.claim_count),
            "creator": str(gl.message.sender_address),
            "evidence_url": evidence_url,
            "expected_content": expected_content,
            "description": description,
            "category": category,
            "status": "pending",
            "votes_for": 0,
            "votes_against": 0,
            "appeal_count": 0,
            "reasoning": "",
            "resolution": json.dumps({
                "verdict": "PENDING",
                "confidence": 0.0,
                "reasoning": "",
                "evidence_summary": ""
            }),
            "created_at": str(int(gl.block.timestamp)),
        }
        self._save_claims(claims)
        gl.emit("ClaimCreated", {
            "claim_id": str(self.claim_count),
            "creator": str(gl.message.sender_address),
            "category": category,
            "evidence_url": evidence_url,
        })
        return str(self.claim_count)

    @gl.public.write
    def resolveClaim(self, claim_id):
        if not self._is_resolver(str(gl.message.sender_address)):
            raise ValueError("Not an approved resolver")

        claims = self._load_claims()
        cid_str = str(claim_id)
        if cid_str not in claims:
            raise ValueError("Claim not found")
        claim = claims[cid_str]
        if claim["status"] != "pending":
            raise ValueError("Claim is already resolved")

        def fetch_evidence():
            response = gl.nondet.web.get(claim["evidence_url"])
            return response.body.decode("utf-8")

        web_content = gl.eq_principle.strict_eq(fetch_evidence)

        task = (
            "Analyze the following claim details and web page content.\n"
            "Expected Content: " + claim["expected_content"] + "\n"
            "Description: " + claim["description"] + "\n"
            "Web Page Content:\n" + web_content[:15000]
        )

        criteria = (
            "Evaluate the claim objectively like a judge. Return STRICTLY in JSON format:\n"
            '{\n    "verdict": "VERIFIED" | "REJECTED" | "INCONCLUSIVE",\n'
            '    "confidence": number 0.0-1.0,\n'
            '    "reasoning": "brief reasoning",\n'
            '    "evidence_summary": "summary"\n}'
        )

        def run_llm_judgment():
            raw_response = gl.nondet.exec_prompt(task + "\nCriteria:\n" + criteria)
            if isinstance(raw_response, dict):
                return json.dumps(raw_response)
            return raw_response

        llm_raw_response = gl.eq_principle.strict_eq(run_llm_judgment)

        try:
            data = json.loads(llm_raw_response)
        except Exception:
            raise ValueError("Invalid LLM response")

        verdict = str(data.get("verdict", "INCONCLUSIVE")).upper().strip()
        confidence = float(data.get("confidence", 0.0))
        reasoning = str(data.get("reasoning", ""))
        evidence_summary = str(data.get("evidence_summary", ""))

        if verdict not in ["VERIFIED", "REJECTED", "INCONCLUSIVE"]:
            verdict = "INCONCLUSIVE"
        if not (0.0 <= confidence <= 1.0):
            confidence = 0.0
            verdict = "INCONCLUSIVE"
        if confidence < 0.7:
            verdict = "INCONCLUSIVE"
            if not reasoning:
                reasoning = "Low confidence threshold not met."

        if verdict == "VERIFIED":
            claim["status"] = "verified"
            claim["votes_for"] = 1
        elif verdict == "REJECTED":
            claim["status"] = "rejected"
            claim["votes_against"] = 1
        else:
            claim["status"] = "inconclusive"

        claim["reasoning"] = reasoning
        claim["resolution"] = json.dumps({
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "evidence_summary": evidence_summary,
        })

        claims[cid_str] = claim
        self._save_claims(claims)

        gl.emit("ClaimResolved", {
            "claim_id": cid_str,
            "verdict": verdict,
            "confidence": str(confidence),
            "resolver": str(gl.message.sender_address),
        })

        return claim["status"]

    @gl.public.write
    def appealClaim(self, claim_id, new_evidence_url=""):
        claims = self._load_claims()
        cid_str = str(claim_id)
        if cid_str not in claims:
            raise ValueError("Claim not found")
        claim = claims[cid_str]

        if str(gl.message.sender_address) != claim["creator"]:
            raise ValueError("Only the claim creator can appeal")

        if claim["status"] == "pending":
            raise ValueError("Claim is still pending")
        if claim["appeal_count"] >= 3:
            raise ValueError("Maximum appeal count reached")

        claim["appeal_count"] += 1
        if new_evidence_url and new_evidence_url.strip() != "":
            claim["evidence_url"] = new_evidence_url.strip()
        claim["status"] = "pending"
        claims[cid_str] = claim
        self._save_claims(claims)

        gl.emit("ClaimAppealed", {
            "claim_id": cid_str,
            "appeal_count": str(claim["appeal_count"]),
            "new_evidence_url": new_evidence_url,
        })

        return "Appeal #" + str(claim["appeal_count"]) + " submitted successfully"

    @gl.public.view
    def getClaim(self, claim_id):
        claims = self._load_claims()
        cid_str = str(claim_id)
        if cid_str not in claims:
            raise ValueError("Claim not found")
        return claims[cid_str]

    @gl.public.view
    def getAllClaims(self):
        return list(self._load_claims().values())

    @gl.public.view
    def getClaimsByStatus(self, status):
        claims = self._load_claims()
        return [c for c in claims.values() if c["status"] == status]

    @gl.public.view
    def getClaimsByCategory(self, category):
        claims = self._load_claims()
        return [c for c in claims.values() if c["category"] == category]

    @gl.public.view
    def getResolvers(self):
        return self._load_resolvers()

    @gl.public.view
    def getStats(self):
        claims = self._load_claims()
        total = len(claims)
        verified = sum(1 for c in claims.values() if c["status"] == "verified")
        rejected = sum(1 for c in claims.values() if c["status"] == "rejected")
        inconclusive = sum(1 for c in claims.values() if c["status"] == "inconclusive")
        success_rate = float(verified / total) if total > 0 else 0.0
        return {
            "total_claims": str(total),
            "verified": str(verified),
            "rejected": str(rejected),
            "inconclusive": str(inconclusive),
            "success_rate": str(success_rate),
        }

    @gl.public.write
    def addResolver(self, resolver_address):
        if str(gl.message.sender_address) != self.owner:
            raise ValueError("Only owner can add resolvers")
        resolvers = self._load_resolvers()
        resolvers[str(resolver_address)] = True
        self._save_resolvers(resolvers)

    @gl.public.write
    def removeResolver(self, resolver_address):
        if str(gl.message.sender_address) != self.owner:
            raise ValueError("Only owner can remove resolvers")
        resolvers = self._load_resolvers()
        resolvers[str(resolver_address)] = False
        self._save_resolvers(resolvers)

    def _load_claims(self):
        claims_data = getattr(self, "claims", "{}")
        if isinstance(claims_data, str):
            return json.loads(claims_data) if claims_data else {}
        return claims_data if claims_data is not None else {}

    def _save_claims(self, claims):
        self.claims = json.dumps(claims)

    def _load_resolvers(self):
        resolvers_data = getattr(self, "resolvers", "{}")
        if isinstance(resolvers_data, str):
            return json.loads(resolvers_data) if resolvers_data else {}
        return resolvers_data if resolvers_data is not None else {}

    def _save_resolvers(self, resolvers):
        self.resolvers = json.dumps(resolvers)

    def _is_resolver(self, address):
        resolvers = self._load_resolvers()
        return bool(resolvers.get(str(address), False))
