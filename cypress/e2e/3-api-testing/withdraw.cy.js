
const CryptoJS = require('crypto-js');
// 000421
describe("withdrawal notification", () => {

    // --- Declare all transaction-related variables here ---
    let terminalSecret = "38a6b08f";
    let terminalId = 'DFTY17';
    let contractCode = '2MPT007f';  
    let httpMethod = "POST";
    let merchantId = '2057LA100006759';
    let date = '2025-10-16';
    let mid = '';  
    let agentId = '';  
    let aid = '';  
    let cExp = '2302';
    let aCode = '';  
    let stan = '000816';  //000421
    let rrn = '000000' + stan; 
    let mti = '0200';  
    let ps = '001000';  
    let mPan = '496009******0755';  
    let amount = '565705';  
    let timestamp = date.replaceAll("-", "") +'160312'
    let responseCode = '00';  
    let variant = 'WITHDRAWAL';  
    let hPan = contractCode + '|' + mPan;  
    let searchKey = date.replaceAll("-", "") + "0200" + mPan.substring(0, 5) + mPan.substring(mPan.length - 4) + terminalId + rrn + amount;
    
    // --- Calculate the hash/signature ---
    const hash = terminalSecret + httpMethod + terminalId + mid + agentId + aid + cExp + stan + rrn + mti + ps + mPan + amount + timestamp;
    const signature = CryptoJS.SHA256(hash).toString();
    before("Withdrawal sql query", () => {
        // --- Full SQL insert payload ---
        const payload = {
            query: `
            INSERT INTO aptent_dev.transaction_record
            (
            trace_id, request_time, response_time, hashed_pan, masked_pan, stan, interchange_id, auth_id, root_trace_id, parent_trace_id, original_transaction_id, reversed, message_name,
            response_code, from_account, to_account, request_amount, response_amount, retrieval_reference_number, transaction_currency_code, card_currency_code, service_restriction_code,
            acquiring_institution_country_code, acquiring_institution_identifier, forwarding_institution_code, receiving_institution_Id, transaction_date, transaction_time,
            transmission_date_time, response_interchange_id, card_acceptor_id, terminal_id, card_acceptor_location, transaction_processing_fee, settlement_processing_fee, transaction_fee,
            settlement_fee, settlement_conversion_rate, pos_condition_code, pos_data_code, pos_entry_mode, pos_geo_code, pos_currency_code, pin_capture_code, settlement_date,
            conversion_date, response_from_remote_entity, amount_card_holder_billing, mti, processing_code, request_sent, routing_rule_id, routing_rule_description, authorization_id_response,
            request_additional_amounts, response_additional_amounts, settlement_currency_code, merchant_type, account_identification1, account_identification2, reversal_transaction_id,
            request_interchange_name, response_interchange_name, emv_data_request, emv_data_response, completed, processor_reference_code, transaction_search_key, sink_terminal_id,
            sink_card_acceptor_id, response_code_received, encrypted_pan, expiry_date, card_sequence_number
            )
            VALUES
            (
            NULL, '${date} 08:47:20', '${date} 08:47:21', 'A6ABC11371774FCB844D3FC41E80C234EDC505A5749C275A9ABEC63A825E9CDD7A741AEF3D2274FCD511BF55C291291C23EDAC91295B766901AFEB7F7',
            '${mPan}', '${stan}', '8', NULL, NULL, NULL, NULL, '0', 'pos-message', '${responseCode}', 'Default', 'Default', '${amount}', '${amount}', '${rrn}', '566', NULL, '226',
            NULL, '00000111129', NULL, '666901', '${date} 23:00:00', '${date} 08:47:19', '${date} 08:47:19', '4', '${merchantId}', '8888', 'TEAMAPT LIMITED        LA           LANG',
            NULL, NULL, '0', NULL, '0', '00', '510101513344101', '051', NULL, NULL, '06', NULL, NULL, '1', NULL, '0200', '000000', '1', NULL, NULL, NULL, '[]',
            '[{"amountType":"02","amount":10000,"accountType":"40","currencyCode":"840"},{"amountType":"01","amount":-10000,"accountType":"40","currencyCode":"840"}]', NULL, '6012',
            NULL, '1017521168', NULL, 'REST_INTERCHANGE', 'Postbridge', NULL, NULL, '1', NULL, '${searchKey}', '${terminalId}', '${merchantId}', '${responseCode}', '', '${cExp}', '000'
            );
            `
        };

        cy.request({
            method: "POST",
            url: "http://127.0.0.1:8000/api/withdrawal/",
            body: payload,
            headers: {'Content-Type': 'application/json'},
        }).then((response) => {
            cy.log("Signature: ", signature);
            expect(response.status).to.eq(201);
            expect(response.body.message).to.equal("Query executed successfully");
            cy.writeFile('cypress/fixtures/withdrawal_result.json', response);
        });
    });

    before('Should send a valid XML request', () => {
        const xmlBody = `<?xml version="1.0" encoding="UTF-8"?>
        <withdrawalNotification>
            <stan>${stan}</stan>
            <hPan>${hPan}</hPan>
            <mPan>${mPan}</mPan>
            <rrn>${rrn}</rrn>
            <amount>${amount}</amount>
            <timestamp>${timestamp}</timestamp>
            <mti>${mti}</mti>
            <ps>${ps}</ps>
            <cExp>${cExp}</cExp>
            <resp>${responseCode}</resp>
            <tap>false</tap>
            <rr>true</rr>
            <rep>true</rep>
            <vm>online</vm>
            <tid>${terminalId}</tid>
            <variant>${variant}</variant>
            <loc>lat:7777.719783,long:5.257476,acc:40.0</loc>
        </withdrawalNotification>`;

        cy.request({
            method: 'POST',
            url: 'https://withdrawals.development.moniepoint.com/api/v1/terminals/withdrawal-notification',
            headers: {
                'Content-Type': 'application/xml',
                'X-Auth-Signature': signature,
                'Accept': '*/*'
            },
            body: xmlBody,
            // encoding: 'utf8',
            // failOnStatusCode: false,

        }).then((response) => {
            cy.log('XML API Response:', response);
            expect(response.status).to.eq(200);
            cy.writeFile('cypress/fixtures/withdrawal_result.xml', response.body);
        });
    });

    before("settlement batches, filter", () => {
        cy.request({
            method: "GET",
            url: `http://127.0.0.1:8000/api/settlement/`,
            qs: {"stan": stan, "amount": amount, "date": date}
        }).then((response) => {
            expect(response.status).to.eq(200);
            cy.log("Settlement API response:", response.body);

            // Overwrite the fixture with the latest response
            cy.writeFile('cypress/fixtures/settlement_batches.json', response.body);
        });
    });

    it("settlement Entries, ID retrieve", () => {
        cy.fixture('settlement_batches').then((monnify_json) => {
        const settlement = monnify_json.settlement_batches;   // <-- correct key
        settlement.forEach(row => {
            cy.request({
            method: "GET",
            url: `http://127.0.0.1:8000/api/settlement/entries/`,
            qs: {id: row.id, scheme_id: row.business_scheme_id}
        }).then((response) => {
            expect(response.status).to.eq(200);
            cy.fixture('scheme_code').then((scheme_json) => {
                let result  = response.body.entry;
                let expected = scheme_json[row.business_scheme_id]; // whole json

                Object.keys(result).forEach(p_type => {
                    let js_data = expected[p_type] // json
                    let py_array = result[p_type] //python
                    let py_data = Object.assign({}, ...py_array)
                    
                    Object.entries(js_data).forEach(([k, v]) => {
                        if(k === "transaction_type") expect(py_data[k]).to.eq(v)
                        else {
                            const found = v.some(e => py_data[k].includes(e));
                            expect(found).to.be.true;
                    }
                        })
                    })

                })

            }
        )
        }
    )

    })

    });
});

