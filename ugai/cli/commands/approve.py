def approve(request_id,decision):
 if decision not in {"approve","reject"}: raise ValueError("decision must be approve or reject")
 raise NotImplementedError("approval store and identity binding are not configured")
