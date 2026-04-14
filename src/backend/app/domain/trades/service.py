from __future__ import annotations

from datetime import datetime, timezone

from app.domain.shared.errors import NotFoundError
from app.domain.trades.entities import (
    DiscTradeFieldRecord,
    DiscTradeInstrumentRecord,
    DiscTradeLegRecord,
    DiscTradePremiumRecord,
    DiscTradeRecord,
    DiscTradeSettlementRecord,
    TradeMasterRecord,
)
from app.domain.trades.enums import TradeTypeCode
from app.domain.trades.repository import TradeUnitOfWorkFactory
from app.domain.trades.schemas import DiscTradeCreateRequest


class TradeApplicationService:
    def __init__(self, uow_factory: TradeUnitOfWorkFactory):
        self._uow_factory = uow_factory

    def list_trade_types(self, id_org: int):
        with self._uow_factory() as uow:
            return uow.list_trade_types(id_org=id_org)

    def list_trades(self, id_org: int):
        with self._uow_factory() as uow:
            return uow.list_trades(id_org=id_org)

    def get_disc_trade(self, id_org: int, id_spe: int):
        with self._uow_factory() as uow:
            aggregate = uow.get_disc_trade(id_org=id_org, id_spe=id_spe)
            if aggregate is None:
                raise NotFoundError(f"DISC trade {id_spe} was not found for organisation {id_org}.")
            return aggregate

    def create_disc_trade(self, payload: DiscTradeCreateRequest):
        with self._uow_factory() as uow:
            trade_type = uow.get_trade_type_by_code(id_org=payload.id_org, code=TradeTypeCode.DISC)
            booked_at = datetime.now(timezone.utc)
            id_spe = uow.next_id_spe(id_org=payload.id_org)
            id_trade = uow.next_id_trade(id_org=payload.id_org)

            master_trade = TradeMasterRecord(
                id_trade=id_trade,
                id_org=payload.id_org,
                id_spe=id_spe,
                id_type=trade_type.id_type,
                type_code=trade_type.code,
                id_f=payload.id_f,
                booked_by=payload.booked_by,
                booked_at=booked_at,
                last_modified_by=None,
                last_modified_at=None,
                status=payload.status,
            )
            uow.add_master_trade(master_trade)

            disc_trade = DiscTradeRecord(
                id_spe=id_spe,
                id_org=payload.id_org,
                id_book=payload.id_book,
                id_portfolio=payload.id_portfolio,
                id_ctpy=payload.id_ctpy,
                id_label=payload.id_label,
                ice_trade_id=payload.ice_trade_id,
                external_id=payload.external_id,
                description=payload.description,
                trade_name=payload.trade_name,
                trade_date=payload.trade_date,
                creation_time=payload.creation_time or booked_at,
                last_update_time=payload.last_update_time,
                volume=payload.volume,
                ice_status=payload.ice_status,
                originating_action=payload.originating_action,
            )
            uow.add_disc_trade(disc_trade)

            for leg_payload in payload.legs:
                id_leg = uow.next_id_leg(id_org=payload.id_org)
                leg = DiscTradeLegRecord(
                    id_leg=id_leg,
                    id_org=payload.id_org,
                    id_disc=id_spe,
                    id_ac=leg_payload.id_ac,
                    leg_id=leg_payload.leg_id,
                    leg_code=leg_payload.leg_code,
                    direction=leg_payload.direction,
                    notional=leg_payload.notional,
                    id_ccy=leg_payload.id_ccy,
                )
                uow.add_disc_leg(leg)

                if leg_payload.instrument is not None:
                    uow.add_disc_instrument(
                        DiscTradeInstrumentRecord(
                            id_inst=uow.next_id_instrument(id_org=payload.id_org),
                            id_org=payload.id_org,
                            id_leg=id_leg,
                            id_ac=leg_payload.instrument.id_ac,
                            notional=leg_payload.instrument.notional,
                            id_ccy=leg_payload.instrument.id_ccy,
                            buysell=leg_payload.instrument.buysell,
                            i_type=leg_payload.instrument.i_type,
                            trade_date=leg_payload.instrument.trade_date,
                            isin=leg_payload.instrument.isin,
                            bbg_ticker=leg_payload.instrument.bbg_ticker,
                            payload_json=leg_payload.instrument.payload_json,
                        )
                    )

                if leg_payload.premium is not None:
                    uow.add_disc_premium(
                        DiscTradePremiumRecord(
                            id_prem=uow.next_id_premium(id_org=payload.id_org),
                            id_org=payload.id_org,
                            id_leg=id_leg,
                            amount=leg_payload.premium.amount,
                            id_ccy=leg_payload.premium.id_ccy,
                            p_date=leg_payload.premium.p_date,
                            markup=leg_payload.premium.markup,
                            total=leg_payload.premium.total,
                            payload_json=leg_payload.premium.payload_json,
                        )
                    )

                if leg_payload.settlement is not None:
                    uow.add_disc_settlement(
                        DiscTradeSettlementRecord(
                            id_settle=uow.next_id_settlement(id_org=payload.id_org),
                            id_org=payload.id_org,
                            id_leg=id_leg,
                            s_date=leg_payload.settlement.s_date,
                            id_ccy=leg_payload.settlement.id_ccy,
                            settlement_type=leg_payload.settlement.settlement_type,
                            payload_json=leg_payload.settlement.payload_json,
                        )
                    )

                if leg_payload.fields is not None:
                    uow.add_disc_fields(
                        DiscTradeFieldRecord(
                            id_field=uow.next_id_field(id_org=payload.id_org),
                            id_org=payload.id_org,
                            id_leg=id_leg,
                            id_ccy=leg_payload.fields.id_ccy,
                            d_date=leg_payload.fields.d_date,
                            notional=leg_payload.fields.notional,
                            payout_ccy_id=leg_payload.fields.payout_ccy_id,
                            buysell=leg_payload.fields.buysell,
                            i_type=leg_payload.fields.i_type,
                        )
                    )

            aggregate = uow.get_disc_trade(id_org=payload.id_org, id_spe=id_spe)
            if aggregate is None:
                raise NotFoundError(f"DISC trade {id_spe} could not be loaded after creation.")

            uow.commit()
            return aggregate
