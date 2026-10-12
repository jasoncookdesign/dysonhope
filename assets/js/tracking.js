// Click tracking for Google Tag Manager.
//
// One delegated click listener turns the declarative data attributes on links
// and buttons into dataLayer events:
//
// - [data-track="true"] elements push a "dysonhope_event" with the element's
//   data-entity, data-action, data-target, data-platform, data-page-type,
//   data-release-title, data-mix-title and data-cta-type values.
// - Every mailto: link (tracked or not, including footers) also pushes a
//   "generate_lead" event.
//
// Nothing is pushed unless the visitor accepted analytics on the cookie consent
// bar, the same gate that loads GTM. Email addresses, phone numbers and query
// strings are never pushed.
(function (window, document) {
	"use strict";

	var CONSENT_KEY = "dh_cookie_consent"; // must match the consent loader in each page's <head>
	var TRACK_SELECTOR = '[data-track="true"]';
	var PAYLOAD_KEYS = {
		entity: "entity",
		action: "action",
		target: "target",
		platform: "platform",
		page_type: "pageType",
		release_title: "releaseTitle",
		mix_title: "mixTitle",
		cta_type: "ctaType"
	};

	function hasConsent() {
		try {
			return window.localStorage.getItem(CONSENT_KEY) === "accepted";
		} catch (error) {
			return false;
		}
	}

	function cleanText(value) {
		if (typeof value !== "string") {
			return undefined;
		}
		var text = value.replace(/\s+/g, " ").trim();
		if (!text || /@/.test(text) || text.replace(/\D/g, "").length >= 7) {
			return undefined; // empty, or looks like an email address or phone number
		}
		return text;
	}

	function cleanUrl(value) {
		if (!value || /^(mailto|tel|sms|javascript):/i.test(value)) {
			return undefined;
		}
		try {
			var url = new URL(value, window.location.origin);
			if (!/^https?:$/.test(url.protocol)) {
				return undefined;
			}
			url.search = "";
			url.hash = "";
			return url.toString();
		} catch (error) {
			return undefined;
		}
	}

	function push(payload) {
		window.dataLayer = window.dataLayer || [];
		window.dataLayer.push(payload);
	}

	function trackedClickPayload(element) {
		var payload = { event: "dysonhope_event" };
		Object.keys(PAYLOAD_KEYS).forEach(function (key) {
			var value = cleanText(element.dataset[PAYLOAD_KEYS[key]]);
			if (value) {
				payload[key] = value;
			}
		});
		var linkText = cleanText(element.textContent) || cleanText(element.getAttribute("aria-label"));
		if (linkText) {
			payload.link_text = linkText;
		}
		var linkUrl = cleanUrl(element.getAttribute("href"));
		if (linkUrl) {
			payload.link_url = linkUrl;
		}
		return Object.keys(payload).length > 1 ? payload : null;
	}

	document.addEventListener("click", function (event) {
		var origin = event.target;
		if (!origin || typeof origin.closest !== "function" || !hasConsent()) {
			return;
		}

		var tracked = origin.closest(TRACK_SELECTOR);
		if (tracked) {
			var payload = trackedClickPayload(tracked);
			if (payload) {
				push(payload);
			}
		}

		var link = origin.closest("a[href]");
		if (link && /^mailto:/i.test(link.getAttribute("href"))) {
			push({ event: "generate_lead", method: "email" });
		}
	});
})(window, document);
