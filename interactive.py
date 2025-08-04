import asyncio

import discord

from nd_prover import *


class SessionExit(Exception):
    pass


LOGIC_KEY = {
    '1️⃣': (TFL, '1️⃣ - TFL'),
    '2️⃣': (FOL, '2️⃣ - FOL'),
    '3️⃣': (MLK, '3️⃣ - MLK'),
    '4️⃣': (MLT, '4️⃣ - MLT'),
    '5️⃣': (MLS4, '5️⃣ - MLS4'),
    '6️⃣': (MLS5, '6️⃣ - MLS5'),
}

ACTION_KEY = {
    '➡️': (2, 'Begin a new subproof'),
    '⬅️': (3, 'End the current subproof'),
    '↔️': (4, 'End the current subproof and begin a new one'),
}

ACTIVE_PROOF_SESSIONS = {}


# Helper functions
def cb(s):
    return f'```\n{s}\n```'


def parse_and_verify_formula(f, logic):
    f = parse_formula(f)
    if logic is TFL and is_tfl_sentence(f):
        return f
    if logic is FOL and is_fol_sentence(f):
        return f
    if issubclass(logic, MLK) and is_ml_sentence(f):
        return f
    raise ParsingError('Invalid formula.')


def parse_and_verify_premises(s, logic):
    s = s.strip()
    if s == 'NA':
        return []
    parts = [p for p in re.split(r'[,;]', s) if p.strip()]
    return [parse_and_verify_formula(p, logic) for p in parts]


def get_selected_action(user_reactions):
    for emoji in ACTION_KEY:
        if emoji in user_reactions:
            return ACTION_KEY[emoji][0]
    return 1


def perform_action(proof, action, s):
    s = s.strip()
    match action:
        case 1:
            if s == 'delete':
                proof.delete_line()
            else:
                f, j = parse_line(s)
                proof.add_line(f, j)
        case 2:
            a = parse_assumption(s)
            proof.begin_subproof(a)
        case 3:
            f, j = parse_line(s)
            proof.end_subproof(f, j)
        case 4:
            a = parse_assumption(s)
            proof.end_and_begin_subproof(a)


async def fetch_latest_msg(msg):
    return await msg.channel.fetch_message(msg.id)


async def get_user_reactions(msg, user_id):
    user_reactions = []
    for r in msg.reactions:
        async for user in r.users():
            if user.id == user_id:
                user_reactions.append(str(r.emoji))
                break
    return user_reactions


async def get_user_input(ctx, bot, session, check=None):
    if check is None:
        def check(msg):
            return (msg.author.id == session.user_id 
                    and msg.channel == session.channel)
    
    while True:
        user_msg = await bot.wait_for('message', check=check)
        cmd = user_msg.content.strip().lower()
        
        if cmd == 'info':
            continue
        if cmd == 'pause':
            await user_msg.add_reaction('✅')
            await ctx.send(cb('Paused. Type "continue" to resume.'))
            def is_continue(msg):
                return (msg.author.id == session.user_id 
                        and msg.channel == session.channel 
                        and msg.content.strip().lower() == 'continue')
            
            next_msg = await bot.wait_for('message', check=is_continue)
            await next_msg.add_reaction('✅')
            continue
        if cmd == 'end':
            await user_msg.add_reaction('✅')
            del ACTIVE_PROOF_SESSIONS[session.user_id]
            raise SessionExit()
        return user_msg


class ProofSession:
    def __init__(self, user_id, channel):
        self.user_id = user_id
        self.channel = channel

        self.logic = None
        self.premises = None
        self.conclusion = None
        self.proof = None
        self.proof_msg = None


async def begin_proof(ctx, bot):
    """
    Begin an interactive proof session.
    """
    # Check for existing session
    if ctx.author.id in ACTIVE_PROOF_SESSIONS:
        await ctx.send('You already have an active proof session!')
        return

    session = ProofSession(ctx.author.id, ctx.channel)
    ACTIVE_PROOF_SESSIONS[ctx.author.id] = session
    try:
        await select_logic(ctx, bot, session)
    except SessionExit:
        return


async def select_logic(ctx, bot, session):
    """
    Send the logic selection prompt.
    """
    logic_key_str = '\n'.join(v[1] for v in LOGIC_KEY.values())
    prompt = 'Select logic:\n\n' + logic_key_str
    bot_msg = await ctx.send(cb(prompt))

    for emoji in LOGIC_KEY:
        await bot_msg.add_reaction(emoji)

    # Wait for user reaction
    def check(reaction, user):
        return (user.id == session.user_id
                and reaction.message.id == bot_msg.id
                and str(reaction.emoji) in LOGIC_KEY)

    try:
        reaction, _ = await bot.wait_for(
            'reaction_add', check=check, timeout=120
        )
    except asyncio.TimeoutError:
        prompt = 'Session timed out. Please try again.'
        await bot_msg.edit(content=cb(prompt))
        await bot_msg.clear_reactions()
        del ACTIVE_PROOF_SESSIONS[session.user_id]
        return
    
    # Delete prompt and set logic
    await bot_msg.delete()
    session.logic = LOGIC_KEY[str(reaction.emoji)][0]
    await input_premises(ctx, bot, session)


async def input_premises(ctx, bot, session):
    """
    Ask the user to enter premises.
    """
    prompt = 'Enter premises (separated by "," or ";"), or "NA" if none:'
    bot_msg = await ctx.send(cb(prompt))
    user_msg = await get_user_input(ctx, bot, session)

    while True:
        try:
            s, logic = user_msg.content, session.logic
            session.premises = parse_and_verify_premises(s, logic)
            await user_msg.delete()
            await bot_msg.delete()
            break
        except ParsingError as e:
            error_msg = await ctx.send(cb(f'{e} Please try again.'))
            next_user_msg = await get_user_input(ctx, bot, session)
            await error_msg.delete()
            await user_msg.delete()
            user_msg = next_user_msg

    await input_conclusion(ctx, bot, session)


async def input_conclusion(ctx, bot, session):
    """
    Ask the user to enter the conclusion.
    """ 
    bot_msg = await ctx.send(cb('Enter conclusion:'))
    user_msg = await get_user_input(ctx, bot, session)

    while True:
        try:
            f, logic = user_msg.content, session.logic
            session.conclusion = parse_and_verify_formula(f, logic)
            await user_msg.delete()
            await bot_msg.delete()
            break
        except ParsingError as e:
            error_msg = await ctx.send(cb(f'{e} Please try again.'))
            next_user_msg = await get_user_input(ctx, bot, session)
            await error_msg.delete()
            await user_msg.delete()
            user_msg = next_user_msg

    # Set up initial proof object
    session.proof = Proof(session.logic, session.premises, session.conclusion)
    await proof_session_loop(ctx, bot, session)


async def send_proof_msg(ctx, session):
    """
    Send the current proof state.
    """
    premises = ', '.join(str(p) for p in session.premises)
    first_line = f'Proof of {premises} ∴ {session.conclusion}'
    content = f'{first_line}\n{'-' * len(first_line)}\n\n{session.proof}'

    # Delete previous proof message, if it exists
    if session.proof_msg:
        try:
            await session.proof_msg.delete()
        except discord.NotFound:
            pass

    session.proof_msg = await ctx.send(cb(content))
    return session.proof_msg


async def proof_session_loop(ctx, bot, session):
    """
    Handles main proof actions until proof is complete.
    """
    proof_msg = await send_proof_msg(ctx, session)
    for emoji in ACTION_KEY:
        await proof_msg.add_reaction(emoji)
    user_msg = await get_user_input(ctx, bot, session)

    while True:
        proof_msg = await fetch_latest_msg(proof_msg)
        user_reactions = await get_user_reactions(proof_msg, session.user_id)

        if len(user_reactions) > 1:
            prompt = 'Only one reaction allowed. Please try again.'
            error_msg = await ctx.send(cb(prompt))
            next_user_msg = await get_user_input(ctx, bot, session)
            await error_msg.delete()
            await user_msg.delete()
            user_msg = next_user_msg
            continue

        action = get_selected_action(user_reactions)

        try:
            perform_action(session.proof, action, user_msg.content)
            await user_msg.delete()
        except Exception as e:
            error_msg = await ctx.send(cb(f'{e} Please try again.'))
            next_user_msg = await get_user_input(ctx, bot, session)
            await error_msg.delete()
            await user_msg.delete()
            user_msg = next_user_msg
            continue

        proof_msg = await send_proof_msg(ctx, session)
        if session.proof.is_complete():
            break
        for emoji in ACTION_KEY:
            await proof_msg.add_reaction(emoji)
        user_msg = await get_user_input(ctx, bot, session)

    await ctx.send(cb('Proof complete! 🎉'))
    del ACTIVE_PROOF_SESSIONS[session.user_id]
